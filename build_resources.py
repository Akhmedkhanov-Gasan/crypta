from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parent
ASSET_ROOT = PROJECT_ROOT / "assets"
OUTPUT_PATH = PROJECT_ROOT / "release" / "resources.pak"

EXCLUDED_SUFFIXES = {
    ".psd",
    ".tiled-project",
    ".tiled-session",
}


def main():
    if not ASSET_ROOT.is_dir():
        raise FileNotFoundError(f"Assets directory not found: {ASSET_ROOT}")

    files = sorted(
        path
        for path in ASSET_ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() not in EXCLUDED_SUFFIXES
    )

    if not files:
        raise RuntimeError("No resources found")

    entries = []
    names = set()

    for path in files:
        path.resolve().relative_to(ASSET_ROOT)
        name = path.relative_to(PROJECT_ROOT).as_posix()
        key = name.casefold()

        if key in names:
            raise ValueError(f"Duplicate resource name: {name}")

        names.add(key)
        entries.append((path, name))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = OUTPUT_PATH.with_suffix(".pak.tmp")

    with ZipFile(
        temporary_path,
        "w",
        compression=ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for path, name in entries:
            archive.write(path, arcname=name)

    with ZipFile(temporary_path, "r") as archive:
        damaged_file = archive.testzip()

    if damaged_file is not None:
        raise RuntimeError(f"Archive verification failed: {damaged_file}")

    temporary_path.replace(OUTPUT_PATH)

    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Packed files: {len(entries)}")
    print(f"Archive size: {size_mb:.1f} MiB")
    print(f"Archive: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()