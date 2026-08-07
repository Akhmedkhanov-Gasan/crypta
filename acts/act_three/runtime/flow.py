from acts.act_one.settings import PLAYER_STARTING_STATS
from acts.act_three.settings import (
    DEBUG_PLAYER_DAMAGE_MAX,
    DEBUG_PLAYER_DAMAGE_MIN,
    DEBUG_PLAYER_POTION_COUNT,
    SUBCLASS_BASE_STATS,
)
from acts.act_two.settings import CLASS_BASE_STATS
from game.combat_log import add_log_message
from game.factories import create_floor_state, create_game_state
from acts.player_stats import apply_player_stat_transition
from levels import FLOOR_CONFIGS
from presentation.layout import (
    ACT_THREE_AWAKENING_END_MS,
    ACT_THREE_NARRATIVE_READY_MS,
)
from settings import CLASS_ABILITY_KILLS


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
        CLASS_BASE_STATS[player_class],
    )

    debug_player.health = debug_player.max_health
    debug_player.damage_min = DEBUG_PLAYER_DAMAGE_MIN
    debug_player.damage_max = DEBUG_PLAYER_DAMAGE_MAX
    debug_player.potion_count = DEBUG_PLAYER_POTION_COUNT
    debug_player.ability_kill_charge = CLASS_ABILITY_KILLS

    return debug_state


def advance_act_three_transition(game_state, current_time):
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
    debug_state.act_three_transition_open = True
    debug_state.act_three_transition_started_at = current_time

    return debug_state


def choose_subclass(game_state, subclass):
    game_state.player.subclass = subclass
    apply_player_stat_transition(
        game_state.player,
        CLASS_BASE_STATS[game_state.player.player_class],
        SUBCLASS_BASE_STATS[subclass],
    )
    if not game_state.act_three_test_mode:
        game_state.floor_index += 1
        game_state.floor = create_floor_state(game_state.floor_index)
        clear_archer_barrage_zone(game_state)
        clear_berserker_crushing_leap(game_state)
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
    add_log_message(
        game_state.combat_log,
        "Act III begins. The world is alive.",
    )


def clear_archer_barrage_zone(game_state):
    player = game_state.player
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    player.archer_barrage_zone_cells.clear()
    player.archer_barrage_shots.clear()


def clear_berserker_crushing_leap(game_state):
    player = game_state.player
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    player.berserker_crushing_leap_origin = None
    player.berserker_crushing_leap_started_at = 0
