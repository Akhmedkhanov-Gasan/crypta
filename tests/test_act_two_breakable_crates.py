import random
import unittest
from unittest.mock import patch

from acts.act_two.crates import break_crate, collect_crate_loot
from acts.act_two.consumables import FIRE_BOMB, POTION
from acts.act_two.settings import CONSUMABLE_BELT_SIZE
from generation import generate_floor
from game.factories import create_game_state
from worldgen.geometry import position_is_in_room


class BreakableCrateGenerationTests(unittest.TestCase):
    def test_regular_floors_have_spread_crates_and_boss_floor_has_none(self):
        random.seed(811)
        first_floor = create_game_state(3).floor
        second_floor = create_game_state(4).floor
        boss_floor = create_game_state(5).floor

        self.assertEqual(len(first_floor.breakable_crates), 7)
        self.assertEqual(len(second_floor.breakable_crates), 9)
        self.assertEqual(boss_floor.breakable_crates, [])
        self.assertEqual(first_floor.potions, [])
        self.assertEqual(second_floor.potions, [])

        for floor in (first_floor, second_floor):
            positions = [
                (crate.column, crate.row)
                for crate in floor.breakable_crates
            ]
            self.assertEqual(len(positions), len(set(positions)))
            self.assertTrue(
                all(crate.variant in (1, 2, 3) for crate in floor.breakable_crates)
            )
            for column, row in positions:
                self.assertTrue(
                    any(
                        floor.map[row + row_change][
                            column + column_change
                        ]
                        in ("#", "S")
                        for column_change, row_change in (
                            (-1, 0),
                            (1, 0),
                            (0, -1),
                            (0, 1),
                        )
                    )
                )
            for index, position in enumerate(positions):
                for other_position in positions[index + 1:]:
                    distance = (
                        abs(position[0] - other_position[0])
                        + abs(position[1] - other_position[1])
                    )
                    self.assertGreaterEqual(distance, 3)

    def test_crates_are_inside_rooms_and_never_in_corridors(self):
        random.seed(813)
        for floor_index in (3, 4):
            floor = generate_floor(floor_index)
            for crate in floor["breakable_crates"]:
                self.assertTrue(
                    any(
                        position_is_in_room(crate["position"], room)
                        for room in floor["rooms"]
                    )
                )


class BreakableCrateLootTests(unittest.TestCase):
    def setUp(self):
        random.seed(812)
        self.game_state = create_game_state(3)
        self.crate = self.game_state.floor.breakable_crates[0]

    def test_most_crates_are_empty(self):
        with patch("acts.act_two.crates.random.random", return_value=0.50):
            self.assertTrue(break_crate(self.game_state, self.crate))

        self.assertTrue(self.crate.is_broken)
        self.assertIsNone(self.crate.loot_kind)
        self.assertFalse(self.crate.loot_available)

    def test_potion_drop_can_be_collected(self):
        with patch("acts.act_two.crates.random.random", return_value=0.20):
            break_crate(self.game_state, self.crate)

        self.assertEqual(self.crate.loot_kind, "potion")
        self.assertTrue(self.crate.loot_available)
        self.assertEqual(
            collect_crate_loot(
                self.game_state,
                (self.crate.column, self.crate.row),
            ),
            "potion",
        )
        self.assertEqual(self.game_state.player.potion_count, 1)
        self.assertFalse(self.crate.loot_available)

    def test_potion_stays_on_ground_when_belt_is_full(self):
        with patch("acts.act_two.crates.random.random", return_value=0.20):
            break_crate(self.game_state, self.crate)
        self.game_state.player.potion_count = CONSUMABLE_BELT_SIZE - 1
        self.game_state.player.act_two.consumable_slots = [
            FIRE_BOMB,
            POTION,
            POTION,
            POTION,
            POTION,
        ]

        self.assertIsNone(
            collect_crate_loot(
                self.game_state,
                (self.crate.column, self.crate.row),
            )
        )
        self.assertEqual(
            self.game_state.player.potion_count,
            CONSUMABLE_BELT_SIZE - 1,
        )
        self.assertTrue(self.crate.loot_available)
        self.assertEqual(
            self.game_state.combat_log[-1],
            "The consumable belt is full.",
        )

    def test_gold_is_the_rarest_drop_and_crate_cannot_be_rerolled(self):
        with patch("acts.act_two.crates.random.random", return_value=0.01):
            self.assertTrue(break_crate(self.game_state, self.crate))
        with patch("acts.act_two.crates.random.random", return_value=0.20):
            self.assertFalse(break_crate(self.game_state, self.crate))

        self.assertEqual(self.crate.loot_kind, "gold")
        self.assertEqual(
            collect_crate_loot(
                self.game_state,
                (self.crate.column, self.crate.row),
            ),
            "gold",
        )
        self.assertEqual(self.game_state.player.gold_count, 1)


if __name__ == "__main__":
    unittest.main()
