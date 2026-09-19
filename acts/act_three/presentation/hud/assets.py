import pygame

import resource_store as resources
from acts.act_three.presentation.hud.layout import (
    get_act_three_hud_layout,
    get_layout_rect,
)
from presentation.layout import ASSET_ROOT


_UI_DIRECTORY = ASSET_ROOT / "ui" / "act_3"

_ART_PATHS = {
    "hud_top_bar_frame": _UI_DIRECTORY / "top_bar_frame.png",
    "hud_hp_fill": _UI_DIRECTORY / "hp_fill.png",
    "hud_xp_fill": _UI_DIRECTORY / "xp_fill.png",
    "hud_journal_panel_frame": (
        _UI_DIRECTORY / "journal_panel_frame.png"
    ),
    "hud_journal_scrollbar_thumb": (
        _UI_DIRECTORY / "journal_scrollbar_thumb.png"
    ),
    "hud_consumable_belt_frame": (
        _UI_DIRECTORY / "consumable_belt_frame.png"
    ),
    "hud_combat_log_frame": (
        _UI_DIRECTORY / "combat_log_frame.png"
    ),
    "hud_gold_icon": _UI_DIRECTORY / "gold_icon.png",
    "hud_camera_frame": _UI_DIRECTORY / "camera_frame.png",
    "hud_tabs_frame": _UI_DIRECTORY / "tabs_frame.png",
    "hud_character_panel_frame": (
        _UI_DIRECTORY / "character_panel_frame.png"
    ),
    "hud_character_panel_button": (
            _UI_DIRECTORY / "button.png"
    ),
    "hud_ability_chains": (
            _UI_DIRECTORY / "chains.png"
    ),
    "hud_rank_level": (
            _UI_DIRECTORY / "level.png"
    ),
}

_ART_RECTS = {
    "hud_top_bar_frame": ("top_bar", "frame"),
    "hud_hp_fill": ("top_bar", "hp_fill"),
    "hud_xp_fill": ("top_bar", "xp_fill"),
    "hud_journal_panel_frame": ("journal_panel", "frame"),
    "hud_journal_scrollbar_thumb": (
        "journal_panel",
        "scrollbar",
        "thumb",
    ),
    "hud_consumable_belt_frame": (
        "down_bar",
        "consumable_belt_frame",
    ),
    "hud_combat_log_frame": (
        "down_bar",
        "combat_log",
        "frame",
    ),
    "hud_gold_icon": ("down_bar", "gold", "icon"),
    "hud_camera_frame": ("down_bar", "camera", "frame"),
    "hud_tabs_frame": ("right_bar", "tabs", "frame"),
    "hud_character_panel_frame": (
        "right_bar",
        "character_panel",
        "frame",
    ),
    "hud_character_panel_button": (
        "right_bar",
        "character_panel",
        "confirm",
        "button",
    ),
    "hud_ability_chains": (
        "down_bar",
        "abilities",
        "slots",
        "ability_q",
        "chains",
    ),
    "hud_rank_level": (
        "right_bar",
        "character_panel",
        "mastery",
        "levels",
        "level_01",
    ),
}

_PORTRAIT_PATHS = {
    "assassin": (
        ASSET_ROOT
        / "act_3"
        / "player"
        / "assassin"
        / "portrait.png"
    ),
    "berserker": (
        ASSET_ROOT
        / "act_3"
        / "player"
        / "berserker"
        / "portrait.png"
    ),
}


def _load_scaled_image(path, rectangle):
    image = resources.load_image(str(path)).convert_alpha()
    return pygame.transform.smoothscale(
        image,
        rectangle.size,
    )


def load_act_three_hud_assets():
    layout = get_act_three_hud_layout()

    assets = {
        "act_three_hud_layout": layout,
    }

    for asset_name, path in _ART_PATHS.items():
        rectangle = get_layout_rect(
            layout,
            *_ART_RECTS[asset_name],
        )
        assets[asset_name] = _load_scaled_image(
            path,
            rectangle,
        )

    portrait_rectangle = get_layout_rect(
        layout,
        "top_bar",
        "portrait",
    )

    assets["hud_portraits"] = {
        subclass: _load_scaled_image(
            path,
            portrait_rectangle,
        )
        for subclass, path in _PORTRAIT_PATHS.items()
    }

    candles_directory = (
        _UI_DIRECTORY / "candles"
    )

    assets["hud_candle_flames"] = {}

    for candle_name in ("small", "large"):
        candle_layout = layout["top_bar"]["candles"][
            candle_name
        ]
        candle_rectangle = get_layout_rect(
            layout,
            "top_bar",
            "candles",
            candle_name,
        )

        assets["hud_candle_flames"][candle_name] = tuple(
            _load_scaled_image(
                candles_directory
                / candle_name
                / frame_name,
                candle_rectangle,
            )
            for frame_name in candle_layout["frames"]
        )

    return assets
