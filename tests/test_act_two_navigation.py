from types import SimpleNamespace

from acts.act_two.navigation import find_act_two_path
from logic import can_player_move_between, get_enemy_attack_targets
from main import _act_two_visual_direction, _movement_direction_for_keys


def _floor(dungeon_map, player=(1, 1)):
    return SimpleNamespace(
        map=dungeon_map,
        player_column=player[0],
        player_row=player[1],
        barriers=set(),
        enemies=[],
        chests=[],
        breakable_crates=[],
    )


def test_player_can_move_diagonally_across_open_floor():
    dungeon_map = ["....", "....", "....", "...."]

    assert can_player_move_between(dungeon_map, 1, 1, 2, 2)


def test_player_cannot_cut_diagonally_through_a_wall_corner():
    dungeon_map = ["....", "..#.", ".#..", "...."]

    assert not can_player_move_between(dungeon_map, 1, 1, 2, 2)


def test_click_path_uses_diagonals_for_a_short_route():
    floor = _floor(["....."] * 5)

    assert find_act_two_path(floor, (3, 3)) == [(2, 2), (3, 3)]


def test_click_path_stays_straight_when_target_is_on_same_row():
    floor = _floor(["......."] * 4)

    assert find_act_two_path(floor, (5, 1)) == [
        (2, 1),
        (3, 1),
        (4, 1),
        (5, 1),
    ]


def test_held_keys_combine_into_diagonal_direction():
    import pygame

    assert _movement_direction_for_keys({pygame.K_s, pygame.K_a}) == (-1, 1)
    assert _act_two_visual_direction((-1, 1)) == (0, 1)
    assert _act_two_visual_direction((1, -1)) == (0, -1)


def test_melee_enemy_can_attack_diagonally_adjacent_player():
    enemy = {
        "column": 1,
        "row": 1,
        "type": "goblin",
        "attack_kind": "melee",
    }

    assert get_enemy_attack_targets(
        ["...."] * 4,
        enemy,
        2,
        2,
        set(),
    ) == [(2, 2)]
