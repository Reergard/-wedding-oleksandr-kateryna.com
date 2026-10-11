"""
Весільний фотоальбом: розділи та їхні фотографії.

Фото імпортуються командою
    python manage.py import_album "<папка з підпапками ВИКУП, РОЗПИС, ...>"
яка складає їх у media/album/<slug>/ (original/, large/, thumb/ + manifest.json).
"""
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage

MEDIA_ALBUM_DIR = Path(settings.MEDIA_ROOT) / "album"
ZIPS_DIR = MEDIA_ALBUM_DIR / "zips"
ALL_ZIP_FOLDER = "Весілля Олександра та Катерини 06.06.2026"


@dataclass(frozen=True)
class AlbumDownload:
    """ZIP-архів з оригіналами для кнопки «Завантажити»."""
    url: str
    filename: str  # назва файлу, під якою архів збережеться у користувача
    size: int

    @property
    def size_label(self) -> str:
        """Розмір по-українськи: «812 МБ», «1,8 ГБ»."""
        mb = self.size / 1024 ** 2
        if mb >= 1024:
            return f"{mb / 1024:.1f} ГБ".replace(".", ",")
        return f"{mb:.0f} МБ"


def _download(zip_name: str, filename: str) -> AlbumDownload | None:
    path = ZIPS_DIR / zip_name
    if not path.is_file():
        return None
    return AlbumDownload(default_storage.url(f"album/zips/{zip_name}"), filename, path.stat().st_size)


def get_album_download() -> AlbumDownload | None:
    return _download("all.zip", f"{ALL_ZIP_FOLDER}.zip")


@dataclass(frozen=True)
class AlbumGroup:
    slug: str
    title: str
    subtitle: str
    icon: str  # шлях у static
    location: str
    photos: list = field(default_factory=list, compare=False)
    download: AlbumDownload | None = None


# Нерозривні пробіли — назва готелю переноситься лише цілком
HOTEL = "OREA HOTEL ANGELO PRAHA"

GROUPS = [
    AlbumGroup("bride-morning", "Ранок нареченої", "Ніжні хвилини перед найважливішим днем",
               "main/img/album-icons/bride-morning.svg",
               "Готель " + HOTEL),
    AlbumGroup("groom-morning", "Ранок нареченого", "Останні приготування та хвилювання",
               "main/img/album-icons/groom-morning.svg",
               HOTEL),
    AlbumGroup("bride-ransom", "Викуп нареченої", "Веселі випробування на шляху до коханої",
               "main/img/album-icons/bride-ransom.svg",
               "Готель " + HOTEL),
    AlbumGroup("ceremony", "Церемонія одруження", "Мить, коли ми сказали «так»",
               "main/img/album-icons/ceremony.svg",
               "Замок Pruhonice"),
    AlbumGroup("photoshoot", "Фотосесія молодят", "Лише ми двоє і наше кохання",
               "main/img/album-icons/photoshoot.svg",
               "Замок Pruhonice"),
    AlbumGroup("banquet", "Весільний банкет", "Свято, танці та найщиріші тости",
               "main/img/album-icons/banquet.svg",
               "Ресторан Green Garden"),
]


@dataclass(frozen=True)
class AlbumPhoto:
    thumb: str
    large: str
    original: str
    original_name: str
    width: int
    height: int

    @property
    def ratio(self) -> str:
        """Співвідношення сторін для CSS (крапка як роздільник незалежно від локалі)."""
        return f"{self.width / self.height:.4f}"


@lru_cache(maxsize=32)
def _load_manifest(path: str, mtime: float) -> tuple:
    """Кешується до зміни manifest.json (mtime входить у ключ кешу)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(data.get("photos", []))


def _photos(slug: str) -> list[AlbumPhoto]:
    manifest = MEDIA_ALBUM_DIR / slug / "manifest.json"
    if not manifest.is_file():
        return []
    url = lambda sub, name: default_storage.url(f"album/{slug}/{sub}/{name}")
    return [
        AlbumPhoto(
            thumb=url("thumb", p["file"]),
            large=url("large", p["file"]),
            original=url("original", p["file"]),
            original_name=p["original_name"],
            width=p["width"],
            height=p["height"],
        )
        for p in _load_manifest(str(manifest), manifest.stat().st_mtime)
    ]


def _scan(group: AlbumGroup) -> AlbumGroup:
    download = _download(f"{group.slug}.zip", f"{group.title} — весілля Олександра та Катерини.zip")
    return AlbumGroup(group.slug, group.title, group.subtitle, group.icon, group.location,
                      _photos(group.slug), download)


def get_groups() -> list[AlbumGroup]:
    return [_scan(g) for g in GROUPS]


def get_group(slug: str) -> tuple[AlbumGroup | None, AlbumGroup | None, AlbumGroup | None]:
    """Повертає (попередній, поточний, наступний) розділ — для навігації між розділами."""
    groups = get_groups()
    for i, g in enumerate(groups):
        if g.slug == slug:
            return groups[i - 1], g, groups[(i + 1) % len(groups)]
    return None, None, None
