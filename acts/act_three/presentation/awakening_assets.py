import pygame

import resource_store as resources
from presentation.layout import ASSET_ROOT
from settings import GAME_WIDTH


def _scale_to_width(source, target_width):
    source_width, source_height = source.get_size()
    target_height = round(
        source_height * target_width / source_width
    )
    return pygame.transform.smoothscale(
        source,
        (target_width, target_height),
    )


def load_act_three_transition_assets():
    ui_directory = ASSET_ROOT / "ui" / "act_3"
    awakening_directory = ui_directory / "awakening"

    background_source = resources.load_image(
        str(ui_directory / "awakening_background_v2.png")
    ).convert()

    assets = {
        "background": _scale_to_width(
            background_source,
            round(GAME_WIDTH * 1.12),
        ),
    }

    for subclass in (
        "berserker",
        "paladin",
        "assassin",
        "archer",
        "warlock",
        "summoner",
    ):
        source = resources.load_image(
            str(awakening_directory / f"{subclass}.png")
        ).convert_alpha()

        assets[f"{subclass}_portrait"] = (
            pygame.transform.smoothscale(
                source,
                (230, 230),
            )
        )

    for player_class in ("warrior", "rogue", "mage"):
        for pose in ("open", "clenched"):
            hands = _scale_to_width(
                resources.load_image(
                    str(
                        ui_directory
                        / f"{player_class}_hands_{pose}.png"
                    )
                ).convert_alpha(),
                GAME_WIDTH,
            )
            hands.fill(
                (185, 190, 200, 255),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            assets[f"{player_class}_hands_{pose}"] = hands

    return assets
