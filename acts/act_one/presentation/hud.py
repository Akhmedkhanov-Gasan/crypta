import pygame

from acts.act_one.interface import draw_sidebar
from acts.act_one.presentation.intro import act_one_intro_hud_opacity
from acts.act_one.presentation.warden_floor import draw_warden_status
from acts.act_one.warden_intro import warden_intro_hud_opacity
from presentation.status import draw_status


def draw_act_one_hud(
    screen,
    game_state,
    heading_font,
    text_font,
    status_font,
    gameplay_assets,
    current_time,
):
    opacity = min(
        act_one_intro_hud_opacity(
            getattr(game_state, "act_one_intro", None),
            current_time,
        ),
        warden_intro_hud_opacity(
            game_state.floor,
            current_time,
        ),
    )

    if opacity <= 0:
        return

    target = screen
    if opacity < 255:
        target = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    draw_status(
        target,
        status_font,
        game_state.floor_index,
        game_state.player.health,
        game_state.floor.enemies,
        game_state.game_won,
    )
    living_warden = next(
        (
            enemy
            for enemy in game_state.floor.enemies
            if (
                enemy.type == "warden"
                and enemy.health > 0
                and enemy.is_active
            )
        ),
        None,
    )
    if living_warden is not None:
        draw_warden_status(
            target,
            living_warden,
            status_font,
            current_time,
        )
    draw_sidebar(
        target,
        heading_font,
        text_font,
        game_state.combat_log,
        game_state.player.health,
        game_state.player.max_health,
        game_state.player.potion_count,
        gameplay_assets,
    )

    if target is not screen:
        target.set_alpha(opacity)
        screen.blit(target, (0, 0))
