import unittest

from game.factories import create_game_state
from levels import FLOOR_CONFIGS
from systems.player_actions import _resolve_stairs


class ActOneProgressionTests(unittest.TestCase):
    def test_act_one_has_no_chests_or_key_carriers(self):
        for floor_index in range(3):
            game_state = create_game_state(floor_index)

            self.assertEqual(game_state.floor.chests, [])
            self.assertFalse(
                any(enemy.has_key for enemy in game_state.floor.enemies)
            )

    def test_act_one_places_exactly_six_potions(self):
        potion_counts = [
            len(create_game_state(floor_index).floor.potions)
            for floor_index in range(3)
        ]

        self.assertEqual(potion_counts, [2, 2, 2])
        self.assertEqual(sum(potion_counts), 6)

    def test_first_two_descents_grant_fixed_upgrade_counts(self):
        for floor_index, expected_count in ((0, 1), (1, 2)):
            game_state = create_game_state(floor_index)
            for enemy in game_state.floor.enemies:
                enemy.health = 0
            game_state.floor.player_column = (
                game_state.floor.stairs_column
            )
            game_state.floor.player_row = game_state.floor.stairs_row

            player_acted = _resolve_stairs(
                game_state,
                first_act_final_floor=2,
            )

            self.assertFalse(player_acted)
            self.assertTrue(game_state.upgrade_screen_open)
            self.assertEqual(
                game_state.act_one_upgrades_remaining,
                expected_count,
            )
            self.assertEqual(
                expected_count,
                FLOOR_CONFIGS[floor_index]["act_floor"],
            )


if __name__ == "__main__":
    unittest.main()
