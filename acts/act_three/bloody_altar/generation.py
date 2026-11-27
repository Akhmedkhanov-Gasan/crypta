from acts.act_three.npc_generation import find_fixture_position, occupy_fixture


def place_random_altar(floor):
    if floor.get("act_three_bloody_altar") is not None:
        return
    position, _ = find_fixture_position(floor, (1, 1))
    floor["act_three_bloody_altar"] = {"position": position, "offers": [], "claimed": False}
    occupy_fixture(floor, position, (1, 1))
