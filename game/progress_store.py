from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys


@dataclass(frozen=True)
class MetaProgress:
    highest_act_reached: int = 1
    menu_theme: int = 1


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
        menu_theme = int(saved_data.get("menu_theme", highest_act))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return MetaProgress()

    highest_act = max(1, min(3, highest_act))
    menu_theme = max(1, min(highest_act, menu_theme))
    return MetaProgress(
        highest_act_reached=highest_act,
        menu_theme=menu_theme,
    )


def save_progress(progress, path=None):
    progress_path = Path(path) if path is not None else get_progress_path()
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = progress_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(
            {
                "version": 2,
                "highest_act_reached": progress.highest_act_reached,
                "menu_theme": progress.menu_theme,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary_path.replace(progress_path)


def record_act_reached(progress, act, path=None):
    if act <= progress.highest_act_reached:
        return progress

    updated_progress = MetaProgress(
        highest_act_reached=act,
        menu_theme=act,
    )

    try:
        save_progress(updated_progress, path)
    except OSError:
        pass

    return updated_progress


def select_menu_theme(progress, theme, path=None):
    if not 1 <= theme <= progress.highest_act_reached:
        return progress

    updated_progress = MetaProgress(
        highest_act_reached=progress.highest_act_reached,
        menu_theme=theme,
    )
    try:
        save_progress(updated_progress, path)
    except OSError:
        pass

    return updated_progress
