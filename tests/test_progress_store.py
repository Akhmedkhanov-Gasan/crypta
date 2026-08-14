import json

from game.progress_store import (
    MetaProgress,
    load_progress,
    record_act_reached,
    select_menu_theme,
)


def test_legacy_progress_defaults_to_latest_unlocked_theme(tmp_path):
    progress_path = tmp_path / "progress.json"
    progress_path.write_text(
        json.dumps({"highest_act_reached": 2}),
        encoding="utf-8",
    )

    progress = load_progress(progress_path)

    assert progress == MetaProgress(highest_act_reached=2, menu_theme=2)


def test_menu_theme_selection_is_saved(tmp_path):
    progress_path = tmp_path / "progress.json"
    progress = MetaProgress(highest_act_reached=3, menu_theme=3)

    updated = select_menu_theme(progress, 1, progress_path)

    assert updated.menu_theme == 1
    assert load_progress(progress_path).menu_theme == 1


def test_reaching_new_act_selects_its_menu_theme(tmp_path):
    progress = MetaProgress(highest_act_reached=1, menu_theme=1)

    updated = record_act_reached(progress, 2, tmp_path / "progress.json")

    assert updated == MetaProgress(highest_act_reached=2, menu_theme=2)
