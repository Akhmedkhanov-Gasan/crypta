import random
import unittest

from acts.act_two.state import TreasuryTrialPhase
from acts.act_two.treasury import (
    activate_treasury_trial,
    purchase_treasury_reward_upgrade,
    update_treasury_trial,
)
from game.factories import create_floor_state, create_game_state
from logic import can_move_to
from systems.player_actions import try_move_player


class ActTwoTreasuryTests(unittest.TestCase):
    def setUp(self):
        random.seed(17)

    def test_treasury_is_generated_only_on_regular_act_two_floors(self):
        for floor_index in (3, 4):
            floor = create_floor_state(floor_index)
            treasury = floor.treasury_room
            self.assertIsNotNone(treasury)
            self.assertEqual(
                floor.map[treasury.chest_position[1]][
                    treasury.chest_position[0]
                ],
                "H",
            )
            self.assertTrue(
                all(
                    floor.map[row][column] == "T"
                    for column, row in treasury.statue_positions
                )
            )
            chest_column, chest_row = treasury.chest_position
            self.assertEqual(
                set(treasury.statue_positions),
                {
                    (chest_column - 1, chest_row),
                    (chest_column + 1, chest_row),
                },
            )

        self.assertIsNone(create_floor_state(5).treasury_room)

    def test_activating_treasury_seals_gate_and_spawns_four_enemies(self):
        game_state = create_game_state(floor_index=3)
        treasury = game_state.floor.treasury_room
        enemy_count = len(game_state.floor.enemies)

        self.assertTrue(activate_treasury_trial(game_state))

        trial_enemies = [
            enemy
            for enemy in game_state.floor.enemies
            if enemy.treasury_trial_enemy
        ]
        self.assertEqual(len(game_state.floor.enemies), enemy_count + 4)
        self.assertEqual(
            sorted(enemy.type for enemy in trial_enemies),
            ["archer", "archer", "brute", "brute"],
        )
        self.assertTrue(all(enemy.is_aggro for enemy in trial_enemies))
        self.assertEqual(treasury.phase, TreasuryTrialPhase.ACTIVE)
        door_column, door_row = treasury.door_position
        self.assertEqual(game_state.floor.map[door_row][door_column], "G")
        self.assertFalse(
            can_move_to(game_state.floor.map, door_column, door_row)
        )

    def test_defeating_trial_enemies_replaces_chest_with_reward(self):
        game_state = create_game_state(floor_index=3)
        treasury = game_state.floor.treasury_room
        activate_treasury_trial(game_state)
        for enemy in game_state.floor.enemies:
            if enemy.treasury_trial_enemy:
                enemy.health = 0

        self.assertTrue(update_treasury_trial(game_state))

        self.assertEqual(
            treasury.phase,
            TreasuryTrialPhase.REWARD_AVAILABLE,
        )
        door_column, door_row = treasury.door_position
        chest_column, chest_row = treasury.chest_position
        self.assertEqual(game_state.floor.map[door_row][door_column], ".")
        self.assertTrue(
            can_move_to(game_state.floor.map, door_column, door_row)
        )
        self.assertEqual(game_state.floor.map[chest_row][chest_column], "R")
        self.assertFalse(game_state.upgrade_screen_open)

    def test_reward_grants_one_gold_upgrade_without_leaving_floor(self):
        game_state = create_game_state(floor_index=3)
        game_state.player.player_class = "warrior"
        game_state.player.gold_count = 0
        treasury = game_state.floor.treasury_room
        activate_treasury_trial(game_state)
        for enemy in game_state.floor.enemies:
            if enemy.treasury_trial_enemy:
                enemy.health = 0
        update_treasury_trial(game_state)

        chest_column, chest_row = treasury.chest_position
        game_state.floor.player_column = chest_column
        game_state.floor.player_row = chest_row + 1
        self.assertTrue(
            try_move_player(
                game_state,
                chest_column,
                chest_row,
                first_act_final_floor=2,
                transition_started_at=100,
            )
        )
        self.assertTrue(game_state.upgrade_screen_open)
        self.assertTrue(game_state.upgrade_reward_pending)
        self.assertEqual(game_state.player.gold_count, 1)

        previous_rank = game_state.player.attribute_ranks["strength"]
        floor_index_before_upgrade = game_state.floor_index
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
