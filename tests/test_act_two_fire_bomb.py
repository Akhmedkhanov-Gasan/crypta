import unittest
from unittest.mock import patch

from acts.act_two.crates import collect_crate_loot
from acts.act_two.consumables import (
    FIRE_BOMB,
    advance_fire_zones,
    fire_bomb_zone_cells,
    get_act_two_consumable_slots,
    is_valid_fire_bomb_target,
    throw_fire_bomb,
)
from game.factories import create_game_state


def _open_three_by_three_target(dungeon_map, avoided_position):
    for row in range(1, len(dungeon_map) - 1):
        for column in range(1, len(dungeon_map[row]) - 1):
            target = (column, row)
            if (
                max(
                    abs(column - avoided_position[0]),
                    abs(row - avoided_position[1]),
                )
                <= 2
            ):
                continue
            cells = fire_bomb_zone_cells(dungeon_map, target)
            if len(cells) == 9:
                return target
    raise AssertionError("No open 3x3 target found")


class FireBombTests(unittest.TestCase):
    def setUp(self):
        self.game_state = create_game_state(3)
        self.floor = self.game_state.floor
        self.player = self.game_state.player
        self.player_position = (
            self.floor.player_column,
            self.floor.player_row,
        )

    def test_act_two_starts_with_one_fire_bomb(self):
        slots = get_act_two_consumable_slots(self.player)

        self.assertEqual(slots.count(FIRE_BOMB), 1)
        self.assertEqual(len(slots), 5)

    def test_zone_is_clipped_to_walkable_cells(self):
        dungeon_map = [
            "#####",
            "#...#",
            "#..##",
            "#...#",
            "#####",
        ]

        self.assertEqual(
            set(fire_bomb_zone_cells(dungeon_map, (2, 2))),
            {
                (1, 1),
                (2, 1),
                (3, 1),
                (1, 2),
                (2, 2),
                (1, 3),
                (2, 3),
                (3, 3),
            },
        )

    def test_target_must_be_visible_and_walkable(self):
        target = _open_three_by_three_target(
            self.floor.map,
            self.player_position,
        )
        self.assertFalse(is_valid_fire_bomb_target(self.game_state, target))

        self.floor.visible_cells.add(target)

        self.assertTrue(is_valid_fire_bomb_target(self.game_state, target))

    def test_throw_deals_nine_total_ticks_and_consumes_slot(self):
        target = _open_three_by_three_target(
            self.floor.map,
            self.player_position,
        )
        self.floor.visible_cells.add(target)
        enemy = self.floor.enemies[0]
        enemy.column, enemy.row = target
        enemy.health = 20
        enemy.max_health = 20

        self.assertTrue(throw_fire_bomb(self.game_state, 0, target, 100))
        self.assertIsNone(self.player.act_two.consumable_slots[0])
        self.assertEqual(enemy.health, 19)
        self.assertEqual(len(self.floor.fire_zones), 1)

        advance_fire_zones(self.game_state)
        self.assertEqual(enemy.health, 19)

        for _ in range(8):
            advance_fire_zones(self.game_state)

        self.assertEqual(enemy.health, 11)
        self.assertEqual(self.floor.fire_zones, [])

    def test_fire_hurts_player_on_burning_cell(self):
        target = self.player_position
        self.floor.visible_cells.add(target)
        previous_health = self.player.health

        self.assertTrue(throw_fire_bomb(self.game_state, 0, target, 100))

        self.assertEqual(self.player.health, previous_health - 1)

    def test_fire_breaks_crate_and_burns_unclaimed_loot_after_two_turns(self):
        target = _open_three_by_three_target(
            self.floor.map,
            self.player_position,
        )
        self.floor.visible_cells.add(target)
        crate = self.floor.breakable_crates[0]
        crate.column, crate.row = target

        with patch("acts.act_two.crates.random.random", return_value=0.20):
            self.assertTrue(throw_fire_bomb(self.game_state, 0, target, 100))

        self.assertTrue(crate.is_broken)
        self.assertEqual(crate.loot_kind, "potion")
        self.assertTrue(crate.loot_available)
        self.assertEqual(crate.loot_fire_turns_remaining, 2)

        advance_fire_zones(self.game_state)
        self.assertEqual(crate.loot_fire_turns_remaining, 2)

        advance_fire_zones(self.game_state)
        self.assertTrue(crate.loot_available)
        self.assertEqual(crate.loot_fire_turns_remaining, 1)

        advance_fire_zones(self.game_state)
        self.assertFalse(crate.loot_available)
        self.assertIsNone(crate.loot_fire_turns_remaining)
        self.assertEqual(
            self.game_state.combat_log[-1],
            "The dropped potion burns away.",
        )

    def test_fire_bomb_crate_loot_can_be_collected_before_it_burns(self):
        target = _open_three_by_three_target(
            self.floor.map,
            self.player_position,
        )
        self.floor.visible_cells.add(target)
        crate = self.floor.breakable_crates[0]
        crate.column, crate.row = target

        with patch("acts.act_two.crates.random.random", return_value=0.20):
            throw_fire_bomb(self.game_state, 0, target, 100)
        advance_fire_zones(self.game_state)
        advance_fire_zones(self.game_state)

        self.assertEqual(
            collect_crate_loot(self.game_state, target),
            "potion",
        )
        self.assertFalse(crate.loot_available)
        self.assertIsNone(crate.loot_fire_turns_remaining)


if __name__ == "__main__":
    unittest.main()
