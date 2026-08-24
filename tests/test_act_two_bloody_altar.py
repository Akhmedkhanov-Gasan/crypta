import unittest

from acts.act_two.abilities import ability_charge_required
from acts.act_two.bloody_altar import (
    BLOOD_HUNGER,
    BROKEN_SEAL,
    GLASS_HEART,
    OPEN_WOUND,
    adjusted_consumable_healing,
    confirm_bloody_pact,
    interact_with_bloody_altar,
    select_bloody_pact,
)
from game.factories import create_game_state
from systems.player_combat import damage_player, resolve_enemy_defeat


class BloodyAltarTests(unittest.TestCase):
    def make_state(self):
        state = create_game_state(4)
        state.player.player_class = "warrior"
        return state

    def accept(self, state, pact_id):
        self.assertTrue(interact_with_bloody_altar(state))
        self.assertTrue(select_bloody_pact(state, pact_id))
        self.assertTrue(confirm_bloody_pact(state))

    def test_random_altar_generates_on_second_act_two_floor(self):
        self.assertIsNotNone(self.make_state().floor.bloody_altar)
        self.assertIsNone(create_game_state(5).floor.bloody_altar)

    def test_test_altar_generates_next_to_first_floor_trader(self):
        floor = create_game_state(3).floor

        self.assertIsNotNone(floor.trader)
        self.assertIsNotNone(floor.bloody_altar)
        distance = (
            abs(floor.trader.column - floor.bloody_altar.column)
            + abs(floor.trader.row - floor.bloody_altar.row)
        )
        self.assertEqual(distance, 1)

    def test_glass_heart_changes_damage_and_maximum_health(self):
        state = self.make_state()
        previous = (
            state.player.damage_min,
            state.player.damage_max,
            state.player.max_health,
        )

        self.accept(state, GLASS_HEART)

        self.assertEqual(state.player.damage_min, previous[0] + 1)
        self.assertEqual(state.player.damage_max, previous[1] + 1)
        self.assertEqual(state.player.max_health, previous[2] - 4)

    def test_broken_seal_destroys_rune_and_halves_charge_requirement(self):
        state = self.make_state()
        state.player.act_two.selected_rune_id = "rune_of_impact"

        self.accept(state, BROKEN_SEAL)

        self.assertIsNone(state.player.act_two.selected_rune_id)
        self.assertEqual(ability_charge_required(state.player), 2)

    def test_open_wound_increases_incoming_damage(self):
        state = self.make_state()
        self.accept(state, OPEN_WOUND)
        previous_health = state.player.health

        dealt = damage_player(state, 2, "magic")

        self.assertEqual(dealt, 3)
        self.assertEqual(state.player.health, previous_health - 3)

    def test_blood_hunger_halves_consumable_healing_and_heals_on_kill(self):
        state = self.make_state()
        self.accept(state, BLOOD_HUNGER)
        self.assertEqual(adjusted_consumable_healing(state.player, 6), 3)

        state.player.health = state.player.max_health - 2
        enemy = next(enemy for enemy in state.floor.enemies if enemy.health > 0)
        enemy.health = 0
        resolve_enemy_defeat(state, enemy)

        self.assertEqual(state.player.health, state.player.max_health - 1)


if __name__ == "__main__":
    unittest.main()
