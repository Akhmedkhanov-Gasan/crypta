import random
import unittest

from game.factories import create_game_state
from systems.player_combat import remove_enemy_corpses_at_position


class EnemyCorpseRemovalTests(unittest.TestCase):
    def test_player_death_position_removes_only_corpses_on_that_cell(self):
        random.seed(811)
        game_state = create_game_state(4)
        floor = game_state.floor
        player_position = (floor.player_column, floor.player_row)
        corpses_on_player = floor.enemies[:2]
        corpse_elsewhere = floor.enemies[2]
        living_enemy_on_player = floor.enemies[3]

        for corpse in corpses_on_player:
            corpse.health = 0
            corpse.column, corpse.row = player_position

        corpse_elsewhere.health = 0
        living_enemy_on_player.column, living_enemy_on_player.row = (
            player_position
        )

        remove_enemy_corpses_at_position(floor, player_position)

        self.assertTrue(
            all(corpse not in floor.enemies for corpse in corpses_on_player)
        )
        self.assertIn(corpse_elsewhere, floor.enemies)
        self.assertIn(living_enemy_on_player, floor.enemies)


if __name__ == "__main__":
    unittest.main()
