import random
import unittest

from acts.act_two.state import SpikeTrapPhase
from acts.act_two.traps import advance_spike_traps
from game.factories import create_game_state


class SpikeTrapGenerationTests(unittest.TestCase):
    def test_regular_act_two_floors_are_sparse_and_boss_floor_is_empty(self):
        random.seed(1202)
        first_floor = create_game_state(3).floor
        second_floor = create_game_state(4).floor
        boss_floor = create_game_state(5).floor

        self.assertEqual(len(first_floor.spike_traps), 5)
        self.assertEqual(len(second_floor.spike_traps), 7)
        self.assertEqual(boss_floor.spike_traps, [])

        for floor in (first_floor, second_floor):
            positions = [
                (trap.column, trap.row)
                for trap in floor.spike_traps
            ]
            self.assertTrue(
                all(
                    trap.phase is SpikeTrapPhase.SAFE
                    for trap in floor.spike_traps
                )
            )
            self.assertEqual(len(positions), len(set(positions)))
            for index, position in enumerate(positions):
                for other_position in positions[index + 1:]:
                    distance = (
                        abs(position[0] - other_position[0])
                        + abs(position[1] - other_position[1])
                    )
                    self.assertGreaterEqual(distance, 5)


class SpikeTrapCycleTests(unittest.TestCase):
    def setUp(self):
        random.seed(2204)
        self.game_state = create_game_state(3)
        self.trap = self.game_state.floor.spike_traps[0]

    def test_active_phase_hits_player_but_never_enemy(self):
        floor = self.game_state.floor
        player = self.game_state.player
        enemy = floor.enemies[0]
        floor.player_column = self.trap.column
        floor.player_row = self.trap.row
        enemy.column = self.trap.column
        enemy.row = self.trap.row
        starting_player_health = player.health
        starting_enemy_health = enemy.health

        advance_spike_traps(self.game_state)

        self.assertIs(self.trap.phase, SpikeTrapPhase.WARNING)
        self.assertEqual(player.health, starting_player_health)
        self.assertEqual(enemy.health, starting_enemy_health)

        advance_spike_traps(self.game_state)

        self.assertIs(self.trap.phase, SpikeTrapPhase.ACTIVE)
        self.assertEqual(player.health, starting_player_health - 3)
        self.assertEqual(enemy.health, starting_enemy_health)

        advance_spike_traps(self.game_state)

        self.assertIs(self.trap.phase, SpikeTrapPhase.COOLDOWN)
        self.assertEqual(player.health, starting_player_health - 3)
        self.assertEqual(enemy.health, starting_enemy_health)

    def test_trap_cannot_kill_or_claim_rewards_for_enemy(self):
        floor = self.game_state.floor
        enemy = floor.enemies[0]
        enemy.column = self.trap.column
        enemy.row = self.trap.row
        enemy.health = 1
        enemy.has_key = True
        player_position = (floor.player_column, floor.player_row)

        advance_spike_traps(self.game_state)
        advance_spike_traps(self.game_state)

        self.assertEqual(enemy.health, 1)
        self.assertEqual(self.game_state.player.enemies_defeated, 0)
        self.assertNotIn((enemy.column, enemy.row), floor.dropped_keys)
        self.assertEqual(
            (floor.player_column, floor.player_row),
            player_position,
        )


if __name__ == "__main__":
    unittest.main()
