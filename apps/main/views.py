from django.http import Http404
from django.shortcuts import render

from .album import get_album_download, get_group, get_groups


def album_index(request):
    """Головна сторінка фотоальбому — картки розділів."""
    groups = get_groups()
    return render(request, "main/album/index.html", {
        "groups": groups,
        "album_download": get_album_download(),
        "total_photos": sum(len(g.photos) for g in groups),
    })


def album_group(request, slug: str):
    """Сторінка окремого розділу альбому з фотографіями."""
    prev_group, group, next_group = get_group(slug)
    if group is None:
        raise Http404("Розділ не знайдено")
    return render(
        request,
        "main/album/group.html",
        {"group": group, "prev_group": prev_group, "next_group": next_group},
    )
