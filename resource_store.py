import atexit
from fnmatch import fnmatchcase
from functools import lru_cache
from io import BytesIO, TextIOWrapper
from pathlib import Path, PurePosixPath
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pygame


PROJECT_ROOT = Path(__file__).resolve().parent
ASSET_ROOT = PROJECT_ROOT / "assets"
FROZEN = bool(getattr(sys, "frozen", False))
PACKED = FROZEN or "--packed-resources" in sys.argv
ARCHIVE_PATH = (
    PROJECT_ROOT / "resources.pak"
    if FROZEN
    else PROJECT_ROOT / "release" / "resources.pak"
)

_music_stream = None


def _absolute_path(path):
    path = Path(path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _resource_name(path):
    path = _absolute_path(path)
    path.relative_to(ASSET_ROOT)
    return path.relative_to(PROJECT_ROOT).as_posix()


@lru_cache(maxsize=1)
def _archive():
    archive = ZipFile(ARCHIVE_PATH, "r")
    atexit.register(archive.close)
    return archive


@lru_cache(maxsize=1)
def _archive_index():
    entries = {}

    for entry in _archive().infolist():
        if entry.is_dir():
            continue

        key = entry.filename.casefold()
        if key in entries:
            raise ValueError(
                f"Duplicate resource in archive: {entry.filename}"
            )

        entries[key] = entry

    return entries


def open_binary(path):
    if not PACKED:
        return _absolute_path(path).open("rb")

    name = _resource_name(path)
    entry = _archive_index().get(name.casefold())

    if entry is None:
        raise FileNotFoundError(
            f"Resource not found in {ARCHIVE_PATH.name}: {name}"
        )

    return BytesIO(_archive().read(entry))


def open_text(path, encoding="utf-8"):
    return TextIOWrapper(open_binary(path), encoding=encoding)


def is_file(path):
    if not PACKED:
        return _absolute_path(path).is_file()

    return _resource_name(path).casefold() in _archive_index()


def glob_resources(directory, pattern):
    directory = _absolute_path(directory)

    if not PACKED:
        return sorted(
            path
            for path in directory.glob(pattern)
            if path.is_file()
        )

    directory_name = _resource_name(directory).casefold()
    matches = []

    for entry in _archive_index().values():
        member = PurePosixPath(entry.filename)

        if member.parent.as_posix().casefold() != directory_name:
            continue

        if fnmatchcase(member.name.casefold(), pattern.casefold()):
            matches.append(PROJECT_ROOT / entry.filename)

    return sorted(matches)


def load_xml(path):
    with open_binary(path) as source:
        return ET.parse(source)


def load_image(path):
    with open_binary(path) as source:
        return pygame.image.load(source, Path(path).name)


def load_font(path, size):
    if path is None:
        return pygame.font.Font(None, size)

    source = open_binary(path)

    try:
        return pygame.font.Font(source, size)
    except BaseException:
        source.close()
        raise


def load_sound(path):
    with open_binary(path) as source:
        return pygame.mixer.Sound(file=source)


def load_music(path):
    global _music_stream

    with open_binary(path) as source:
        stream = BytesIO(source.read())

    try:
        pygame.mixer.music.load(
            stream,
            Path(path).suffix.lstrip("."),
        )
    except BaseException:
        stream.close()
        raise

    previous_stream = _music_stream
    _music_stream = stream

    if previous_stream is not None:
        previous_stream.close()