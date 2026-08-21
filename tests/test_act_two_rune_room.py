import random
import unittest

from acts.act_two.runes import (
    interact_with_rune_pedestal,
    select_rune,
    strike_wall_rune,
)
from acts.act_two.rune_catalog import RUNES_BY_CLASS
from acts.act_two.state import RunePuzzlePhase
from game.events import GameEventType
from game.factories import create_floor_state, create_game_state
from logic import can_move_to


class ActTwoRuneRoomTests(unittest.TestCase):
    def setUp(self):
        random.seed(17)

    def test_small_rune_room_is_generated_only_on_first_act_two_floor(self):
        floor = create_floor_state(3)
        room = floor.rune_room
        self.assertIsNotNone(room)
        self.assertEqual((room.width, room.height), (5, 5))
        self.assertEqual(len(room.wall_rune_positions), 3)
        self.assertEqual(len(set(room.wall_rune_positions)), 3)
        door_column, door_row = room.door_position
        self.assertTrue(
            all(
                abs(column - door_column) + abs(row - door_row) >= 8
                for column, row in room.wall_rune_positions
            )
        )
        self.assertTrue(
            all(
                floor.map[row][column] == "#"
                for column, row in room.wall_rune_positions
            )
        )
        self.assertTrue(
            all(
                floor.map[row][column] == "r"
                for column, row in room.floor_rune_positions
            )
        )
        pedestal_column, pedestal_row = room.pedestal_position
        self.assertEqual(floor.map[pedestal_row][pedestal_column], "P")
        self.assertFalse(
            can_move_to(floor.map, pedestal_column, pedestal_row)
        )

        self.assertIsNone(create_floor_state(4).rune_room)
        self.assertIsNone(create_floor_state(5).rune_room)

    def test_all_three_wall_runes_awaken_the_pedestal_without_order(self):
        game_state = create_game_state(floor_index=3)
        room = game_state.floor.rune_room
        first_position = room.wall_rune_positions[0]

        self.assertTrue(strike_wall_rune(game_state, first_position, 1234))
        self.assertTrue(strike_wall_rune(game_state, first_position, 5678))
        self.assertEqual(room.activated_runes, {0})
        self.assertEqual(room.activation_effect_started_at, {0: 1234})

        for position in reversed(room.wall_rune_positions[1:]):
            self.assertTrue(strike_wall_rune(game_state, position))

        self.assertEqual(room.activated_runes, {0, 1, 2})
        self.assertEqual(room.phase, RunePuzzlePhase.REWARD_AVAILABLE)

    def test_pedestal_opens_one_class_rune_choice(self):
        game_state = create_game_state(floor_index=3)
        game_state.player.player_class = "warrior"
        game_state.player.gold_count = 0
        room = game_state.floor.rune_room

        self.assertTrue(interact_with_rune_pedestal(game_state))
        self.assertEqual(game_state.player.gold_count, 0)
        self.assertFalse(game_state.upgrade_screen_open)

        for position in room.wall_rune_positions:
            strike_wall_rune(game_state, position)

        floor_index_before_upgrade = game_state.floor_index
        self.assertTrue(interact_with_rune_pedestal(game_state))
        self.assertEqual(room.phase, RunePuzzlePhase.REWARD_AVAILABLE)
        self.assertTrue(game_state.rune_selection_open)
        self.assertIsNone(game_state.player.act_two.selected_rune_id)
        self.assertTrue(
            any(
                event.type is GameEventType.ENVIRONMENT
                and event.data.get("kind") == "rune_selection_opened"
                for event in game_state.events
            )
        )

        self.assertEqual(len(RUNES_BY_CLASS["warrior"]), 3)
        self.assertFalse(
            select_rune(game_state, RUNES_BY_CLASS["mage"][0].id)
        )
        selected_rune = RUNES_BY_CLASS["warrior"][0]
        self.assertTrue(select_rune(game_state, selected_rune.id))
        self.assertEqual(room.phase, RunePuzzlePhase.CLAIMED)
        self.assertFalse(game_state.rune_selection_open)
        self.assertEqual(
            game_state.player.act_two.selected_rune_id,
            selected_rune.id,
        )
        self.assertFalse(
            select_rune(game_state, RUNES_BY_CLASS["warrior"][1].id)
        )
        self.assertEqual(game_state.player.gold_count, 0)
        self.assertFalse(game_state.upgrade_screen_open)
        self.assertFalse(game_state.upgrade_reward_pending)
        self.assertEqual(game_state.floor_index, floor_index_before_upgrade)
        self.assertEqual(game_state.floor_transition_started_at, -1)


if __name__ == "__main__":
    unittest.main()
