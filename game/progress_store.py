from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys


@dataclass(frozen=True)
class MetaProgress:
    highest_act_reached: int = 1


def get_progress_path():
    if sys.platform == "win32":
        data_root = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home() / "AppData" / "Local",
            )
        )
    elif sys.platform == "darwin":
        data_root = Path.home() / "Library" / "Application Support"
    else:
        data_root = Path(
            os.environ.get(
                "XDG_DATA_HOME",
                Path.home() / ".local" / "share",
            )
        )

    return data_root / "Crypta" / "progress.json"


def load_progress(path=None):
    progress_path = Path(path) if path is not None else get_progress_path()

    try:
        saved_data = json.loads(progress_path.read_text(encoding="utf-8"))
        highest_act = int(saved_data.get("highest_act_reached", 1))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return MetaProgress()

    return MetaProgress(highest_act_reached=max(1, highest_act))


def save_progress(progress, path=None):
    progress_path = Path(path) if path is not None else get_progress_path()
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = progress_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(
            {
                "version": 1,
                "highest_act_reached": progress.highest_act_reached,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary_path.replace(progress_path)


def record_act_reached(progress, act, path=None):
    if act <= progress.highest_act_reached:
        return progress

    updated_progress = MetaProgress(highest_act_reached=act)

    try:
        save_progress(updated_progress, path)
    except OSError:
        pass

    return updated_progress
