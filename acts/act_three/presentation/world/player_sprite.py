from acts.act_three.presentation.animation import (
    _idle_frame,
    _stable_text_seed,
)
from acts.act_three.presentation.warlock import (
    warlock_curse_sprite,
    warlock_demon_idle_sprite,
    warlock_demon_transition_sprite,
)
from acts.act_three.presentation.berserker import (
    crushing_leap_direction,
    crushing_leap_frame,
    last_rage_frame,
)
from acts.act_three.presentation.combat_effects import (
    _PLAYER_HIT_SPRITE_DURATION_MS,
    _assassin_death_frame,
    _berserker_death_frame,
    _player_death_frame,
    _warlock_death_frame,
)
from acts.act_three.presentation.player_locomotion import (
    locomotion_sprite,
)
from acts.act_three.presentation.player_motion import (
    assassin_attack_direction,
    assassin_attack_frame,
    assassin_hurt_direction,
    assassin_hurt_frame,
    assassin_idle_frame,
    assassin_shadow_step_direction,
    assassin_walk_direction,
    berserker_hurt_frame,
    berserker_idle_frame,
    warlock_hurt_frame,
    warlock_idle_frame,
)
from acts.act_three.settings import (
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
    BERSERKER_LAST_RAGE_ANIMATION_MS,
)


def select_player_sprite(
    context,
    player_state,
    player,
    assets,
    current_time,
    attack_frame_duration,
):
    if player_state.death_elapsed is not None:
        return (
            _death_sprite(
                player_state.subclass,
                player,
                assets,
                current_time,
            ),
            False,
        )

    if player_state.hurt_sprite_active:
        return (
            _hurt_sprite(
                player_state.subclass,
                player,
                assets,
                current_time,
            ),
            False,
        )

    if player_state.last_rage_activation_active:
        direction = assassin_walk_direction(player.facing_direction)
        frame = last_rage_frame(
            player_state.last_rage_elapsed,
            BERSERKER_LAST_RAGE_ANIMATION_MS,
        )
        return (
            assets[
                f"player_berserker_last_rage_{direction}_{frame}"
            ],
            False,
        )

    if player_state.shadow_step_active:
        direction = assassin_shadow_step_direction(
            context.teleport_origin,
            (
                context.floor.player_column,
                context.floor.player_row,
            ),
        )
        return (
            assets[
                "player_assassin_shadow_step_"
                f"{direction}_{player_state.shadow_step_frame}"
            ],
            False,
        )

    if player_state.shield_charge_active:
        return assets["player_paladin_shield_charge"], False

    if player_state.berserker_leap_travel_active:
        direction = crushing_leap_direction(
            player_state.berserker_leap_origin,
            (
                context.floor.player_column,
                context.floor.player_row,
            ),
        )
        frame = crushing_leap_frame(
            player_state.berserker_leap_elapsed,
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
        )
        return (
            assets[
                "player_berserker_crushing_leap_"
                f"{direction}_{frame}"
            ],
            False,
        )

    if player_state.berserker_leap_impact_active:
        direction = crushing_leap_direction(
            player_state.berserker_leap_origin,
            (
                context.floor.player_column,
                context.floor.player_row,
            ),
        )
        return (
            assets[
                f"player_berserker_crushing_leap_{direction}_7"
            ],
            False,
        )

    if player_state.leap_active:
        return assets["player_archer_leap"], False

    demon_transition_sprite = (
        warlock_demon_transition_sprite(
            player,
            assets,
            current_time,
        )
    )
    if demon_transition_sprite is not None:
        return demon_transition_sprite, False

    curse_sprite = warlock_curse_sprite(
        player,
        assets,
        current_time,
    )
    if curse_sprite is not None:
        return curse_sprite, False

    if 0 <= player_state.attack_elapsed < attack_frame_duration:
        return (
            _attack_sprite(
                player_state.subclass,
                player,
                assets,
                player_state.attack_elapsed,
                attack_frame_duration,
            ),
            False,
        )

    if context.locomotion_pose.active:
        return (
            locomotion_sprite(
                assets,
                player,
                context.locomotion_pose,
            ),
            True,
        )

    return (
        _idle_sprite(
            player_state.subclass,
            player,
            context.floor.visual_seed,
            assets,
            current_time,
        ),
        False,
    )


def _death_sprite(
    player_subclass,
    player,
    assets,
    current_time,
):
    if player_subclass == "assassin":
        death_frame = _assassin_death_frame(player, current_time)
    elif player_subclass == "berserker":
        death_frame = _berserker_death_frame(player, current_time)
    elif player_subclass == "warlock":
        death_frame = _warlock_death_frame(player, current_time)
    else:
        death_frame = _player_death_frame(player, current_time)

    if death_frame is None:
        if player_subclass == "summoner":
            return assets["player_summoner_no_familiar_hurt"]

        if (
            player_subclass == "warlock"
            and player.warlock_demon_form_active
        ):
            direction = assassin_hurt_direction(
                player.facing_direction
            )
            return assets[
                f"player_warlock_demon_hurt_{direction}_0"
            ]

        if player_subclass in ("berserker", "warlock"):
            direction = assassin_hurt_direction(
                player.facing_direction
            )
            return assets[
                f"player_{player_subclass}_hurt_{direction}_0"
            ]

        return assets[f"player_{player_subclass}_hurt"]

    if player_subclass == "berserker":
        direction = assassin_hurt_direction(
            player.facing_direction
        )
        return assets[
            f"player_berserker_death_{direction}_{death_frame}"
        ]

    if (
        player_subclass == "warlock"
        and player.warlock_demon_form_active
    ):
        direction = assassin_hurt_direction(
            player.facing_direction
        )
        return assets[
            (
                "player_warlock_demon_death_"
                f"{direction}_{death_frame}"
            )
        ]

    return assets[
        f"player_{player_subclass}_death_{death_frame}"
    ]


def _hurt_sprite(
    player_subclass,
    player,
    assets,
    current_time,
):
    if player_subclass == "berserker":
        elapsed = current_time - player.hit_animation_started_at
        direction = assassin_hurt_direction(player.facing_direction)
        frame = berserker_hurt_frame(
            elapsed,
            _PLAYER_HIT_SPRITE_DURATION_MS,
        )
        return assets[
            f"player_berserker_hurt_{direction}_{frame}"
        ]

    if player_subclass == "paladin":
        return assets["player_paladin_hurt"]

    if player_subclass == "assassin":
        elapsed = current_time - player.hit_animation_started_at
        direction = assassin_hurt_direction(player.facing_direction)
        frame = assassin_hurt_frame(
            elapsed,
            _PLAYER_HIT_SPRITE_DURATION_MS,
            direction,
        )
        return assets[
            f"player_assassin_hurt_{direction}_{frame}"
        ]

    if player_subclass == "archer":
        return assets["player_archer_hurt"]

    if player_subclass == "warlock":
        elapsed = current_time - player.hit_animation_started_at
        direction = assassin_hurt_direction(
            player.facing_direction
        )
        frame = warlock_hurt_frame(
            elapsed,
            _PLAYER_HIT_SPRITE_DURATION_MS,
        )

        if player.warlock_demon_form_active:
            return assets[
                (
                    "player_warlock_demon_hurt_"
                    f"{direction}_{frame}"
                )
            ]

        return assets[
            f"player_warlock_hurt_{direction}_{frame}"
        ]

    if player.summoner_familiar_active:
        return assets["player_summoner_no_familiar_hurt"]

    return assets["player_summoner_hurt"]


def _attack_sprite(
    player_subclass,
    player,
    assets,
    attack_elapsed,
    attack_frame_duration,
):
    if player_subclass in ("assassin", "berserker", "warlock"):
        direction = assassin_attack_direction(
            player.facing_direction
        )
        frame = assassin_attack_frame(
            attack_elapsed,
            attack_frame_duration,
        )

        if (
            player_subclass == "warlock"
            and player.warlock_demon_form_active
        ):
            return assets[
                (
                    "player_warlock_demon_attack_"
                    f"{direction}_{frame}"
                )
            ]

        return assets[
            f"player_{player_subclass}_attack_{direction}_{frame}"
        ]

    if (
        player_subclass == "summoner"
        and player.summoner_familiar_active
    ):
        return assets["player_summoner_no_familiar_attack"]

    return assets[f"player_{player_subclass}_attack"]


def _idle_sprite(
    player_subclass,
    player,
    visual_seed,
    assets,
    current_time,
):
    if player_subclass == "assassin":
        player_frame = assassin_idle_frame(current_time)
    elif player_subclass == "berserker":
        player_frame = berserker_idle_frame(current_time)
    else:
        player_frame = _idle_frame(
            current_time,
            visual_seed
            ^ _stable_text_seed(f"player:{player_subclass}"),
        )

    if player_subclass in ("assassin", "berserker"):
        direction = assassin_walk_direction(player.facing_direction)
        if direction == "down":
            return assets[
                f"player_{player_subclass}_idle_{player_frame}"
            ]
        return assets[
            f"player_{player_subclass}_idle_{direction}_{player_frame}"
        ]

    if player_subclass == "warlock":
        if player.warlock_demon_form_active:
            return warlock_demon_idle_sprite(
                player,
                assets,
                current_time,
            )

        direction = assassin_walk_direction(player.facing_direction)
        frame = warlock_idle_frame(current_time)
        return assets[
            f"player_warlock_idle_{direction}_{frame}"
        ]

    if (
        player_subclass == "summoner"
        and player.summoner_familiar_active
    ):
        return assets[
            f"player_summoner_no_familiar_idle_{player_frame}"
        ]

    return assets[f"player_{player_subclass}_idle_{player_frame}"]
