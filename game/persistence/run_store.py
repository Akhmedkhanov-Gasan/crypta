from dataclasses import dataclass
from enum import Enum, auto
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from game.progress_store import get_progress_path


RUN_SAVE_VERSION = 1


class RunSaveStatus(Enum):
    MISSING = auto()
    AVAILABLE = auto()
    INVALID = auto()
    INCOMPATIBLE = auto()
    UNREADABLE = auto()


@dataclass(frozen=True)
class RunSaveResult:
    status: RunSaveStatus
    snapshot: dict[str, Any] | None = None
    error: str | None = None


def get_run_save_path() -> Path:
    return get_progress_path().with_name("suspended_run.json")


def load_run_save(path=None) -> RunSaveResult:
    save_path = (
        Path(path)
        if path is not None
        else get_run_save_path()
    )

    try:
        text = save_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return RunSaveResult(RunSaveStatus.MISSING)
    except UnicodeError as error:
        return RunSaveResult(
            RunSaveStatus.INVALID,
            error=str(error),
        )
    except OSError as error:
        return RunSaveResult(
            RunSaveStatus.UNREADABLE,
            error=str(error),
        )

    try:
        saved_data = json.loads(text)
    except (ValueError, RecursionError) as error:
        return RunSaveResult(
            RunSaveStatus.INVALID,
            error=str(error),
        )

    if not isinstance(saved_data, dict):
        return RunSaveResult(RunSaveStatus.INVALID)

    version = saved_data.get("version")

    if type(version) is not int:
        return RunSaveResult(RunSaveStatus.INVALID)

    if version != RUN_SAVE_VERSION:
        return RunSaveResult(RunSaveStatus.INCOMPATIBLE)

    snapshot = saved_data.get("snapshot")

    if not isinstance(snapshot, dict) or not snapshot:
        return RunSaveResult(RunSaveStatus.INVALID)

    return RunSaveResult(
        RunSaveStatus.AVAILABLE,
        snapshot=snapshot,
    )


def write_run_save(snapshot: dict[str, Any], path=None) -> None:
    if not isinstance(snapshot, dict) or not snapshot:
        raise ValueError("Run snapshot must be a non-empty dictionary")

    serialized = json.dumps(
        {
            "version": RUN_SAVE_VERSION,
            "snapshot": snapshot,
        },
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
    )

    save_path = (
        Path(path)
        if path is not None
        else get_run_save_path()
    )
    save_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=save_path.parent,
            prefix=f".{save_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        temporary_path.replace(save_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def delete_run_save(path=None) -> None:
    save_path = (
        Path(path)
        if path is not None
        else get_run_save_path()
    )
    save_path.unlink(missing_ok=True)
