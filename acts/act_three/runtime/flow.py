from acts.act_one.settings import (
    PLAYER_STARTING_ATTRIBUTE_RANKS,
    PLAYER_STARTING_STATS,
)
from acts.act_three.settings import SUBCLASS_BASE_STATS
from acts.act_two.settings import (
    CLASS_BASE_ATTRIBUTE_RANKS,
    CLASS_BASE_STATS,
    CLASS_STARTING_STATS,
)
from acts.act_three.abilities import (
    initialize_act_three_progression,
)
from game.combat_log import add_log_message
from game.factories import create_floor_state, create_game_state
from game.attributes import (
    apply_attribute_rank_transition,
    apply_player_stat_transition,
)
from levels import FLOOR_CONFIGS
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    ACT_THREE_NARRATIVE_READY_MS,
)


SECOND_ACT_FINAL_FLOOR = max(
    index
    for index, floor_config in enumerate(FLOOR_CONFIGS)
    if floor_config["act"] == 2
)


def create_oracle_debug_state(
    player_class,
    opening_message,
):
    debug_state = create_game_state(
        floor_index=SECOND_ACT_FINAL_FLOOR,
        opening_message=opening_message,
    )
    debug_player = debug_state.player
    debug_player.player_class = player_class
    apply_player_stat_transition(
        debug_player,
        PLAYER_STARTING_STATS,
        CLASS_STARTING_STATS[player_class],
    )
    apply_attribute_rank_transition(
        debug_player,
        PLAYER_STARTING_ATTRIBUTE_RANKS,
        CLASS_BASE_ATTRIBUTE_RANKS[player_class],
    )

    return debug_state


def advance_act_three_transition(game_state, current_time):
    if game_state.act_three.awakening is not None:
        return
    narrative_elapsed = (
        current_time
        - game_state.act_three_transition_started_at
    )

    if game_state.act_three_visual_started_at == 0:
        if narrative_elapsed < ACT_THREE_NARRATIVE_READY_MS:
            game_state.act_three_transition_started_at = (
                current_time - ACT_THREE_NARRATIVE_READY_MS
            )
        else:
            game_state.act_three_visual_started_at = current_time
        return

    game_state.act_three_visual_started_at = (
        current_time - ACT_THREE_AWAKENING_END_MS
    )


def create_act_three_debug_transition(
    player_class,
    current_time,
):
    debug_state = create_oracle_debug_state(
        player_class,
        (
            "Debug jump: "
            f"{player_class.title()} Act III awakening."
        ),
    )

    for enemy in debug_state.floor.enemies:
        enemy.health = 0

    debug_state.floor.projectiles.clear()
    from acts.act_three.awakening.runtime import begin_awakening, _nearby_cell
    from acts.act_two.presentation.bosses.oracle_death import OracleDeathState
    from acts.act_two.presentation.bosses.oracle_phase_two import OraclePhaseTwoState
    from acts.act_two.visibility import update_act_two_visibility

    floor = debug_state.floor
    oracle = next(enemy for enemy in floor.enemies if enemy.type == "oracle")
    oracle.oracle_phase = 2
    oracle.phase_transition_pending = False
    oracle.oracle_death_started_at = max(1, current_time)
    oracle.oracle_death_elapsed = 5800
    floor.oracle_phase_two = OraclePhaseTwoState(caster=oracle, defeated_pending=True)
    floor.oracle_death = OracleDeathState(
        caster=oracle,
        position=(oracle.column, oracle.row),
        updated_at=current_time,
        camera_origin=(0, 0),
        elapsed=5800,
        finished=True,
    )
    floor.boss_fight_started = True
    floor.oracle_gate_opened = True
    if floor.oracle_intro is not None:
        floor.oracle_intro.finished = True
    floor.player_column, floor.player_row = _nearby_cell(floor, (oracle.column + 4, oracle.row + 3))
    update_act_two_visibility(floor)

    begin_awakening(debug_state, current_time)
    debug_state.act_three.awakening.debug_reveal = True

    return debug_state


def choose_subclass(game_state, subclass):
    from acts.act_three.abilities import get_subclass_definition

    definition = get_subclass_definition(subclass)
    if definition is None or definition.parent_class != game_state.player.player_class:
        return
    if game_state.player.subclass is not None:
        return
    game_state.player.subclass = subclass
    initialize_act_three_progression(
        game_state.player,
    )
    apply_player_stat_transition(
        game_state.player,
        CLASS_BASE_STATS[game_state.player.player_class],
        SUBCLASS_BASE_STATS[subclass],
    )
    scene = game_state.act_three.awakening
    if not game_state.act_three_test_mode and scene is None:
        game_state.floor_index += 1
        game_state.floor = create_floor_state(game_state.floor_index)
        clear_archer_barrage_zone(game_state)
        clear_berserker_crushing_leap(game_state)
        clear_paladin_sacred_ground(game_state)
    game_state.player.key_count = 0
    game_state.player_attack_targets = []
    game_state.subclass_selection_open = False
    display_name = {
        "berserker": "Berserker",
        "paladin": "Paladin",
        "assassin": "Assassin",
        "archer": "Archer",
        "warlock": "Warlock",
        "summoner": "Summoner",
    }[subclass]
    class_name = game_state.player.player_class
    add_log_message(
        game_state.combat_log,
        (
            f"The {class_name} chooses the path "
            f"of the {display_name}."
        ),
    )
    if scene is not None:
        import pygame
        from acts.act_three.awakening.runtime import _set_phase

        _set_phase(scene, "transformation", pygame.time.get_ticks())
        game_state.act_three_transition_open = True
    else:
        add_log_message(game_state.combat_log, "Act III begins. The world is alive.")


def clear_archer_barrage_zone(game_state):
    player = game_state.player
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    player.archer_barrage_zone_cells.clear()
    player.archer_barrage_zones.clear()
    player.archer_barrage_directions.clear()
    player.archer_barrage_hit_turns.clear()
    player.archer_barrage_shots.clear()
    player.archer_barrage_pending_hits.clear()
    game_state.act_three.barrage_turn = None


def clear_berserker_crushing_leap(game_state):
    player = game_state.player
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    player.berserker_crushing_leap_origin = None
    player.berserker_crushing_leap_started_at = 0


def clear_paladin_sacred_ground(game_state):
    player = game_state.player
    player.paladin_sacred_ground_cast_requested = False
    player.paladin_sacred_ground_anchor = None
    player.paladin_sacred_ground_cells.clear()
    player.paladin_sacred_ground_lightnings.clear()
    player.paladin_sacred_ground_turns = 0
    player.paladin_sacred_ground_started_at = 0
