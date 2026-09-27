from dataclasses import dataclass
from typing import Any

from acts.act_three.presentation.combat_effects import (
    _player_death_elapsed,
    _player_hurt_sprite_active,
)
from acts.act_three.presentation.player_motion import (
    assassin_shadow_step_frame,
)
from acts.act_three.settings import (
    ARCHER_LEAP_DURATION_MS,
    ASSASSIN_SHADOW_STEP_DURATION_MS,
    BERSERKER_CRUSHING_LEAP_IMPACT_MS,
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
    BERSERKER_LAST_RAGE_ANIMATION_MS,
    PALADIN_SHIELD_CHARGE_TRAVEL_MS,
)


@dataclass(frozen=True, slots=True)
class PlayerRenderState:
    subclass: str
    attack_elapsed: int
    leap_origin: Any
    leap_started_at: int
    leap_elapsed: int
    leap_active: bool
    berserker_leap_origin: Any
    berserker_leap_started_at: int
    berserker_leap_elapsed: int
    berserker_leap_travel_active: bool
    berserker_leap_impact_active: bool
    last_rage_elapsed: int
    last_rage_activation_active: bool
    shield_charge_origin: Any
    shield_charge_started_at: int
    shield_charge_elapsed: int
    shield_charge_active: bool
    shadow_step_elapsed: int
    shadow_step_active: bool
    shadow_step_frame: int
    hurt_sprite_active: bool
    death_elapsed: Any


def create_player_render_state(
    player,
    teleport_origin,
    transition_started_at,
    current_time,
):
    player_subclass = player.subclass

    if player_subclass not in (
        "berserker",
        "paladin",
        "assassin",
        "archer",
        "warlock",
        "summoner",
    ):
        player_subclass = "berserker"

    attack_elapsed = current_time - player.attack_animation_started_at
    leap_origin = player.archer_leap_origin
    leap_started_at = player.archer_leap_started_at
    leap_elapsed = current_time - leap_started_at
    leap_active = (
        player_subclass == "archer"
        and leap_origin is not None
        and leap_started_at > 0
        and 0 <= leap_elapsed < ARCHER_LEAP_DURATION_MS
    )

    berserker_leap_origin = player.berserker_crushing_leap_origin
    berserker_leap_started_at = (
        player.berserker_crushing_leap_started_at
    )
    berserker_leap_elapsed = (
        current_time - berserker_leap_started_at
    )
    berserker_leap_travel_active = (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and berserker_leap_started_at > 0
        and 0
        <= berserker_leap_elapsed
        < BERSERKER_CRUSHING_LEAP_TRAVEL_MS
    )
    berserker_leap_impact_active = (
        player_subclass == "berserker"
        and berserker_leap_origin is not None
        and (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            <= berserker_leap_elapsed
            < (
                BERSERKER_CRUSHING_LEAP_TRAVEL_MS
                + BERSERKER_CRUSHING_LEAP_IMPACT_MS
            )
        )
    )

    last_rage_elapsed = (
        current_time - player.berserker_last_rage_started_at
    )
    last_rage_activation_active = (
        player_subclass == "berserker"
        and player.berserker_last_rage_started_at > 0
        and 0
        <= last_rage_elapsed
        < BERSERKER_LAST_RAGE_ANIMATION_MS
    )

    shield_charge_origin = player.paladin_shield_charge_origin
    shield_charge_started_at = player.paladin_shield_charge_started_at
    shield_charge_elapsed = current_time - shield_charge_started_at
    shield_charge_active = (
        player_subclass == "paladin"
        and shield_charge_origin is not None
        and shield_charge_started_at > 0
        and 0
        <= shield_charge_elapsed
        < PALADIN_SHIELD_CHARGE_TRAVEL_MS
    )

    shadow_step_elapsed = current_time - transition_started_at
    shadow_step_active = (
        player_subclass == "assassin"
        and teleport_origin is not None
        and transition_started_at > 0
        and 0
        <= shadow_step_elapsed
        < ASSASSIN_SHADOW_STEP_DURATION_MS
    )

    return PlayerRenderState(
        subclass=player_subclass,
        attack_elapsed=attack_elapsed,
        leap_origin=leap_origin,
        leap_started_at=leap_started_at,
        leap_elapsed=leap_elapsed,
        leap_active=leap_active,
        berserker_leap_origin=berserker_leap_origin,
        berserker_leap_started_at=berserker_leap_started_at,
        berserker_leap_elapsed=berserker_leap_elapsed,
        berserker_leap_travel_active=(
            berserker_leap_travel_active
        ),
        berserker_leap_impact_active=(
            berserker_leap_impact_active
        ),
        last_rage_elapsed=last_rage_elapsed,
        last_rage_activation_active=(
            last_rage_activation_active
        ),
        shield_charge_origin=shield_charge_origin,
        shield_charge_started_at=shield_charge_started_at,
        shield_charge_elapsed=shield_charge_elapsed,
        shield_charge_active=shield_charge_active,
        shadow_step_elapsed=shadow_step_elapsed,
        shadow_step_active=shadow_step_active,
        shadow_step_frame=assassin_shadow_step_frame(
            shadow_step_elapsed,
            ASSASSIN_SHADOW_STEP_DURATION_MS,
        ),
        hurt_sprite_active=_player_hurt_sprite_active(
            player,
            current_time,
        ),
        death_elapsed=_player_death_elapsed(
            player,
            current_time,
        ),
    )
