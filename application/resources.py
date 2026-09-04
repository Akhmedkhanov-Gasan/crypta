"""Application-level loading of resources owned by every act."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApplicationResources:
    act_one_fonts: dict[str, Any]
    act_one_gameplay_assets: dict[str, Any]
    act_two_fonts: dict[str, Any]
    act_two_sprites: dict[str, Any]
    act_two_hud_layout: Any
    oracle_ui_layout: Any
    oracle_ui_assets: Any
    act_two_trade_layout: Any
    bloody_altar_layout: Any
    death_score_layout: Any
    death_score_assets: Any
    act_three_fonts: dict[str, Any]
    act_three_gameplay_assets: dict[str, Any]
    act_three_transition_assets: dict[str, Any]
    menu_assets: dict[str, Any]
    menu_layouts: dict[int, Any]
    menu_fonts: dict[int, dict[str, Any]]
    act_one_sounds: Any
    act_two_transition_sounds: Any
    act_two_sounds: Any


def load_application_resources(startup):
    from acts.act_two.presentation.bloody_altar import (
        load_bloody_altar_layout,
    )
    from acts.act_two.presentation.bosses.oracle_ui import load_oracle_ui
    from acts.act_two.presentation.death_score import (
        load_act_two_death_score,
    )
    from presentation.assets import (
        load_act_one_fonts,
        load_act_one_gameplay_assets,
        load_act_three_fonts,
        load_act_three_gameplay_assets,
        load_act_three_transition_assets,
        load_act_two_fonts,
        load_act_two_hud_layout,
        load_act_two_sprites,
        load_act_two_trade_layout,
        load_menu_assets,
        load_menu_layouts,
    )
    from presentation.audio import (
        ActOneSoundBank,
        ActTwoSoundBank,
        ActTwoTransitionSoundBank,
    )
    from presentation.layout import (
        ACT_ONE_SOUNDS_PATH,
        ACT_TWO_SOUNDS_PATH,
    )

    act_one_fonts = startup.load(load_act_one_fonts)
    act_one_gameplay_assets = startup.load(load_act_one_gameplay_assets)

    act_two_fonts = startup.load(load_act_two_fonts)
    act_two_sprites = startup.load(load_act_two_sprites)
    act_two_hud_layout = startup.load(load_act_two_hud_layout)
    oracle_ui_layout, oracle_ui_assets = startup.load(load_oracle_ui)
    act_two_trade_layout = startup.load(load_act_two_trade_layout)
    bloody_altar_layout = startup.load(load_bloody_altar_layout)
    death_score_layout, death_score_assets = startup.load(
        load_act_two_death_score,
        act_two_sprites,
    )

    act_three_fonts = startup.load(load_act_three_fonts)
    act_three_gameplay_assets = startup.load(
        load_act_three_gameplay_assets,
    )
    act_three_transition_assets = startup.load(
        load_act_three_transition_assets,
    )

    menu_assets = startup.load(load_menu_assets)
    menu_layouts = {
        act_number: startup.load(load_menu_layouts, act_number)
        for act_number in (1, 2, 3)
    }
    menu_fonts = {
        act_number: act_two_fonts
        for act_number in (1, 2, 3)
    }

    act_one_sounds = startup.load(
        ActOneSoundBank.load,
        ACT_ONE_SOUNDS_PATH,
    )
    act_two_transition_sounds = startup.load(
        ActTwoTransitionSoundBank.load,
        ACT_TWO_SOUNDS_PATH,
    )
    act_two_sounds = startup.load(
        ActTwoSoundBank.load,
        ACT_TWO_SOUNDS_PATH,
    )

    return ApplicationResources(
        act_one_fonts=act_one_fonts,
        act_one_gameplay_assets=act_one_gameplay_assets,
        act_two_fonts=act_two_fonts,
        act_two_sprites=act_two_sprites,
        act_two_hud_layout=act_two_hud_layout,
        oracle_ui_layout=oracle_ui_layout,
        oracle_ui_assets=oracle_ui_assets,
        act_two_trade_layout=act_two_trade_layout,
        bloody_altar_layout=bloody_altar_layout,
        death_score_layout=death_score_layout,
        death_score_assets=death_score_assets,
        act_three_fonts=act_three_fonts,
        act_three_gameplay_assets=act_three_gameplay_assets,
        act_three_transition_assets=act_three_transition_assets,
        menu_assets=menu_assets,
        menu_layouts=menu_layouts,
        menu_fonts=menu_fonts,
        act_one_sounds=act_one_sounds,
        act_two_transition_sounds=act_two_transition_sounds,
        act_two_sounds=act_two_sounds,
    )
