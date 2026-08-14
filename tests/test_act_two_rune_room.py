import random
import unittest

from acts.act_two.runes import (
    interact_with_rune_pedestal,
    strike_wall_rune,
)
from acts.act_two.state import RunePuzzlePhase
from acts.act_two.treasury import purchase_treasury_reward_upgrade
from game.factories import create_floor_state, create_game_state
from logic import can_move_to


class ActTwoRuneRoomTests(unittest.TestCase):
    def setUp(self):
        random.seed(17)

    def test_small_rune_room_is_generated_only_on_regular_act_two_floors(self):
        for floor_index in (3, 4):
            floor = create_floor_state(floor_index)
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

    def test_pedestal_reward_opens_one_upgrade_and_keeps_current_floor(self):
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
        self.assertEqual(room.phase, RunePuzzlePhase.CLAIMED)
        self.assertEqual(game_state.player.gold_count, 1)
        self.assertTrue(game_state.upgrade_screen_open)
        self.assertTrue(game_state.upgrade_reward_pending)

        previous_rank = game_state.player.attribute_ranks["strength"]
        upgraded, _message = purchase_treasury_reward_upgrade(
            game_state,
            "strength",
        )
        self.assertTrue(upgraded)
        self.assertEqual(
            game_state.player.attribute_ranks["strength"],
            previous_rank + 1,
        )
        self.assertEqual(game_state.player.gold_count, 0)
        self.assertFalse(game_state.upgrade_screen_open)
        self.assertFalse(game_state.upgrade_reward_pending)
        self.assertEqual(game_state.floor_index, floor_index_before_upgrade)
        self.assertEqual(game_state.floor_transition_started_at, -1)


if __name__ == "__main__":
    unittest.main()
