import unittest

from presentation.layout import (
    AWAKENING_FADE_END_MS,
    AWAKENING_HOLD_END_MS,
    AWAKENING_OPEN_END_MS,
    AWAKENING_RECOVERY_BLINK_END_MS,
    AWAKENING_RECOVERY_BLINK_START_MS,
    AWAKENING_SECOND_OPEN_END_MS,
)
from presentation.screens import (
    _awakening_eye_openness,
    _class_attribute_changes,
    _class_selection_data,
)
from game.factories import create_game_state
from main import FIRST_ACT_FINAL_FLOOR, _complete_class_selection


class ActTwoAwakeningTests(unittest.TestCase):
    def test_player_blacks_out_between_two_awakenings(self):
        self.assertEqual(_awakening_eye_openness(0), 0)
        self.assertEqual(_awakening_eye_openness(AWAKENING_OPEN_END_MS), 1)
        self.assertGreater(
            _awakening_eye_openness(AWAKENING_HOLD_END_MS),
            0,
        )
        self.assertEqual(_awakening_eye_openness(AWAKENING_FADE_END_MS), 0)
        self.assertEqual(
            _awakening_eye_openness(AWAKENING_SECOND_OPEN_END_MS),
            1,
        )

    def test_recovery_blink_never_fully_closes_the_eyes(self):
        midpoint = (
            AWAKENING_RECOVERY_BLINK_START_MS
            + AWAKENING_RECOVERY_BLINK_END_MS
        ) // 2
        self.assertGreater(_awakening_eye_openness(midpoint), 0)
        self.assertLess(_awakening_eye_openness(midpoint), 0.5)

    def test_each_class_has_the_old_mans_answer(self):
        responses = {
            name: data["response"]
            for name, data in _class_selection_data().items()
        }
        self.assertEqual(
            responses,
            {
                "warrior": (
                    "Then stand, and let the Crypta break against you."
                ),
                "rogue": (
                    "Then walk where even the Crypta cannot see."
                ),
                "mage": (
                    "Then look deeper. But beware what looks back."
                ),
            },
        )

    def test_class_cards_compare_current_attribute_baselines(self):
        self.assertEqual(
            _class_attribute_changes("warrior"),
            (
                ("STR", 2, 4, 2),
                ("VIT", 2, 5, 3),
            ),
        )
        self.assertEqual(
            _class_attribute_changes("rogue"),
            (
                ("STR", 2, 3, 1),
                ("DEX", 1, 5, 4),
            ),
        )
        self.assertEqual(
            _class_attribute_changes("mage"),
            (
                ("INT", 0, 4, 4),
                ("VIT", 2, 3, 1),
            ),
        )

    def test_choice_finishes_on_the_first_act_two_floor(self):
        game_state = create_game_state(
            floor_index=FIRST_ACT_FINAL_FLOOR,
        )
        game_state.player.player_class = "warrior"
        game_state.class_selection_open = True
        game_state.class_selection_choice = "warrior"
        game_state.class_selection_choice_started_at = 100

        _complete_class_selection(game_state)

        self.assertEqual(game_state.floor_index, FIRST_ACT_FINAL_FLOOR + 1)
        self.assertFalse(game_state.class_selection_open)
        self.assertIsNone(game_state.class_selection_choice)
        self.assertEqual(game_state.class_selection_choice_started_at, 0)
        self.assertIn(
            "fire_bomb",
            game_state.player.act_two.consumable_slots,
        )


if __name__ == "__main__":
    unittest.main()
