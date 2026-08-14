import unittest

from enemies import ENEMY_TYPES
from game.factories import create_game_state
from game.state import EnemyBehaviorState, EnemyState
from logic import get_enemy_attack_targets
from systems.enemy_ai.common import prepare_enemy_attack
from systems.enemy_turn import resolve_enemy_turn


class ActTwoEnemyAttackTests(unittest.TestCase):
    def setUp(self):
        self.dungeon_map = [
            "#########",
            "#.......#",
            "#.......#",
            "#.......#",
            "#.......#",
            "#.......#",
            "#.......#",
            "#.......#",
            "#########",
        ]
        self.brute = {
            "column": 4,
            "row": 4,
            "attack_kind": "cleave",
        }

    def test_brute_cleave_reaches_three_cells_toward_adjacent_player(self):
        targets = get_enemy_attack_targets(
            self.dungeon_map,
            self.brute,
            player_column=4,
            player_row=3,
            blocking_positions=set(),
        )

        self.assertEqual(targets, [(4, 3), (4, 2), (4, 1)])

        targets = get_enemy_attack_targets(
            self.dungeon_map,
            self.brute,
            player_column=5,
            player_row=4,
            blocking_positions=set(),
        )

        self.assertEqual(targets, [(5, 4), (6, 4), (7, 4)])

    def test_brute_cleave_stops_at_blocking_object(self):
        targets = get_enemy_attack_targets(
            self.dungeon_map,
            self.brute,
            player_column=4,
            player_row=5,
            blocking_positions={(4, 6)},
        )

        self.assertEqual(targets, [(4, 5)])

    def test_brute_cleave_requires_player_to_be_adjacent(self):
        targets = get_enemy_attack_targets(
            self.dungeon_map,
            self.brute,
            player_column=4,
            player_row=2,
            blocking_positions=set(),
        )

        self.assertEqual(targets, [])

    def test_brute_attacks_on_the_turn_after_telegraph(self):
        game_state = create_game_state(floor_index=3)
        brute = EnemyState.from_config(
            enemy_type="brute",
            column=4,
            row=4,
            name="Test Brute",
            config=ENEMY_TYPES["brute"],
            belongs_to_boss_group=False,
        )
        brute.is_active = True
        brute.is_aggro = True
        brute.behavior_state = EnemyBehaviorState.CHASING
        game_state.floor.enemies = [brute]
        game_state.floor.map = self.dungeon_map
        game_state.floor.player_column = 4
        game_state.floor.player_row = 3
        game_state.player.dodge_chance = 0
        targets = [(4, 3), (4, 2), (4, 1)]

        prepare_enemy_attack(
            game_state,
            brute,
            targets,
            "cleave",
        )
        health_before_attack = game_state.player.health

        resolve_enemy_turn(
            game_state,
            player_position_before_action=(4, 3),
            rogue_ability_activated=False,
        )

        self.assertLess(game_state.player.health, health_before_attack)
        self.assertEqual(brute.attack_targets, [])
        self.assertEqual(
            brute.behavior_state,
            EnemyBehaviorState.CHASING,
        )
        self.assertEqual(brute.attack_windup_turns_remaining, 0)


if __name__ == "__main__":
    unittest.main()
