"""
Імпорт весільних фото в альбом.

    python manage.py import_album "E:\\wedding_06.06.2026\\фото на сайт"

Для кожного розділу створюється папка media/album/<slug>/ з трьома версіями фото:
    original/  — точна побайтова копія файлу (перевіряється SHA-256), для завантаження;
    large/     — 2560 px по довшій стороні, для перегляду на весь екран;
    thumb/     — 900 px по довшій стороні, для сітки.
та manifest.json з порядком фото і їхніми розмірами.
Наприкінці збираються ZIP-архіви для завантаження (див. build_album_zips).

Команду можна запускати повторно: вже імпортовані фото пропускаються.
"""
import hashlib
import json
import os
import re
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

from apps.main.album import GROUPS, MEDIA_ALBUM_DIR

# Назва папки з фото → slug розділу на сайті
FOLDER_TO_SLUG = {
    "РАНОК НАРЕЧЕНОЇ": "bride-morning",
    "ЗБОРИ НАРЕЧЕНОГО": "groom-morning",
    "ВИКУП": "bride-ransom",
    "РОЗПИС": "ceremony",
    "ФОТОСЕСІЯ": "photoshoot",
    "РЕСТОРАН": "banquet",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SIZES = {"large": (2560, 90), "thumb": (900, 82)}  # довша сторона, якість JPEG


def sort_key(path: Path):
    """Порядок фотографа: «Olga_Kozchenko (13 of 953)» йде перед «(127 of 953)».
    Файли без такого номера (дрон тощо) — наприкінці, за назвою."""
    m = re.search(r"\((\d+) of \d+\)", path.name)
    if m:
        return (0, int(m.group(1)), path.name.lower())
    parts = re.split(r"(\d+)", path.name.lower())
    return (1, 0, [int(p) if p.isdigit() else p for p in parts])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def process_photo(src: str, dest_dir: str, name: str) -> dict:
    """Копіює оригінал і створює web-версії. Виконується в окремому процесі."""
    src_p, dest = Path(src), Path(dest_dir)
    original = dest / "original" / name
    src_hash = sha256(src_p)

    # Під цим номером уже інше фото (набір змінився) — копіюємо заново і перегенеровуємо версії
    fresh = not (original.exists() and sha256(original) == src_hash)
    if fresh:
        shutil.copy2(src_p, original)
        if sha256(original) != src_hash:
            raise RuntimeError(f"Копія пошкоджена: {src}")

    with Image.open(src_p) as im:
        icc = im.info.get("icc_profile")
        im = ImageOps.exif_transpose(im)  # поворот за EXIF (вертикальні фото)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        width, height = im.size
        for folder, (max_side, quality) in SIZES.items():
            out = dest / folder / name
            if out.exists() and not fresh:
                continue
            copy = im.copy()
            copy.thumbnail((max_side, max_side), Image.LANCZOS)
            copy.save(
                out, "JPEG", quality=quality, optimize=True, progressive=True,
                subsampling=0 if folder == "large" else 2,
                icc_profile=icc,  # EXIF (зокрема GPS) у web-версії не потрапляє
            )

    return {"file": name, "original_name": src_p.name, "width": width, "height": height}


class Command(BaseCommand):
    help = "Імпортує фото з папок розділів у весільний альбом (без втрати оригіналів)."

    def add_arguments(self, parser):
        parser.add_argument("source", help="Папка з підпапками ВИКУП, РОЗПИС, ...")
        parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))

    def handle(self, source, workers, **options):
        source = Path(source)
        if not source.is_dir():
            raise CommandError(f"Папку не знайдено: {source}")

        known = {g.slug for g in GROUPS}
        folders = {p.name.upper(): p for p in source.iterdir() if p.is_dir()}
        unknown = set(folders) - set(FOLDER_TO_SLUG)
        if unknown:
            self.stderr.write(self.style.WARNING(f"Пропускаю невідомі папки: {', '.join(sorted(unknown))}"))

        total = 0
        for folder_name, slug in FOLDER_TO_SLUG.items():
            assert slug in known, slug
            folder = folders.get(folder_name)
            if folder is None:
                self.stderr.write(self.style.WARNING(f"Немає папки «{folder_name}» — розділ {slug} пропущено"))
                continue

            files = sorted(
                (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS),
                key=sort_key,
            )
            dest = MEDIA_ALBUM_DIR / slug
            for sub in ("original", *SIZES):
                (dest / sub).mkdir(parents=True, exist_ok=True)

            self.stdout.write(f"{folder_name} -> media/album/{slug}/  ({len(files)} фото)")
            jobs = {}
            with ProcessPoolExecutor(max_workers=workers) as pool:
                for i, src in enumerate(files, 1):
                    name = f"{i:04d}.jpg" if src.suffix.lower() in (".jpg", ".jpeg") else f"{i:04d}{src.suffix.lower()}"
                    jobs[pool.submit(process_photo, str(src), str(dest), name)] = i
                results = {}
                for done, fut in enumerate(as_completed(jobs), 1):
                    results[jobs[fut]] = fut.result()
                    if done % 25 == 0 or done == len(files):
                        self.stdout.write(f"   {done}/{len(files)}")

            photos = [results[i] for i in sorted(results)]
            # прибираємо файли, яких більше немає в наборі
            keep = {p["file"] for p in photos}
            for sub in ("original", *SIZES):
                for f in (dest / sub).iterdir():
                    if f.name not in keep:
                        f.unlink()
            # manifest перезаписуємо лише при змінах — за його датою визначається, чи треба оновити ZIP
            manifest = dest / "manifest.json"
            content = json.dumps({"photos": photos}, ensure_ascii=False, indent=1)
            if not manifest.exists() or manifest.read_text(encoding="utf-8") != content:
                manifest.write_text(content, encoding="utf-8")
            total += len(photos)

        self.stdout.write(self.style.SUCCESS(f"Готово: {total} фото у {MEDIA_ALBUM_DIR}"))
        call_command("build_album_zips", stdout=self.stdout, stderr=self.stderr)
