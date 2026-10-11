"""
ZIP-архіви з оригіналами фото для кнопок «Завантажити».

    python manage.py build_album_zips

Створює media/album/zips/<slug>.zip для кожного розділу та all.zip з усім альбомом.
Фото зберігаються без стиснення (ZIP_STORED): JPEG від стиснення не меншає, а всередині
лежать точні копії оригіналів з їхніми початковими назвами.
Архів перезбирається, лише якщо фото розділу змінились (manifest.json новіший за архів).
Запускається автоматично наприкінці import_album.
"""
import json
import os
import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.main.album import ALL_ZIP_FOLDER, GROUPS, MEDIA_ALBUM_DIR, ZIPS_DIR


def _entries(index: int, group) -> list[tuple[Path, str]]:
    """(шлях до оригіналу, шлях усередині архіву) для фото розділу."""
    folder = MEDIA_ALBUM_DIR / group.slug
    manifest = folder / "manifest.json"
    if not manifest.is_file():
        return []
    photos = json.loads(manifest.read_text(encoding="utf-8"))["photos"]
    return [(folder / "original" / p["file"], f"{index}. {group.title}/{p['original_name']}") for p in photos]


def _write_zip(target: Path, entries: list[tuple[Path, str]]) -> None:
    tmp = target.with_suffix(".zip.part")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for src, arcname in entries:
            zf.write(src, arcname)
    os.replace(tmp, target)  # атомарно: на сайті ніколи не з'явиться недописаний архів


def _is_fresh(target: Path, manifests: list[Path]) -> bool:
    return target.exists() and all(m.stat().st_mtime <= target.stat().st_mtime for m in manifests)


class Command(BaseCommand):
    help = "Збирає ZIP-архіви з оригіналами фото (для кожного розділу та всього альбому)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Перезібрати навіть актуальні архіви")

    def handle(self, force=False, **options):
        ZIPS_DIR.mkdir(parents=True, exist_ok=True)
        all_entries, all_manifests = [], []

        for index, group in enumerate(GROUPS, 1):
            entries = _entries(index, group)
            if not entries:
                continue
            manifest = MEDIA_ALBUM_DIR / group.slug / "manifest.json"
            all_manifests.append(manifest)
            all_entries += [(src, f"{ALL_ZIP_FOLDER}/{arc}") for src, arc in entries]

            target = ZIPS_DIR / f"{group.slug}.zip"
            if not force and _is_fresh(target, [manifest]):
                self.stdout.write(f"   {target.name}: актуальний")
                continue
            self.stdout.write(f"   {target.name}: {len(entries)} фото...")
            _write_zip(target, entries)

        if all_entries:
            target = ZIPS_DIR / "all.zip"
            if force or not _is_fresh(target, all_manifests):
                self.stdout.write(f"   all.zip: {len(all_entries)} фото...")
                _write_zip(target, all_entries)
            else:
                self.stdout.write("   all.zip: актуальний")

        self.stdout.write(self.style.SUCCESS(f"Архіви готові: {ZIPS_DIR}"))
