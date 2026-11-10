from acts.act_three.enemies.generation import (
    populate_act_three_enemies,
)
from acts.act_three.room_generation import (
    attach_act_three_passages,
    generate_tmx_room_floor,
    generate_tmx_sequence_floor,
)
from acts.act_three.tmx_loader import load_tmx_floor
from acts.act_three.layout_generation import generate_room_layout


def build_act_three_floor(
    config,
    floor_index,
    floor_count,
):
    if config.get("exit_map_path"):
        from acts.act_three.trials import trial_map_path

        floor = generate_room_layout(
            config,
            trial_map_path(config.get("trial_subclass")) if config.get("trial_room") else None,
        )
    elif config.get("tmx_room_sequence"):
        from acts.act_three.trials import TRIAL_MAPS, trial_map_path

        sequence = tuple(
            trial_map_path(config.get("trial_subclass"))
            if path == TRIAL_MAPS["assassin"] else path
            for path in config["tmx_room_sequence"]
        )
        floor = generate_tmx_sequence_floor(
            sequence
        )
    elif config.get("room_template_directory"):
        floor = generate_tmx_room_floor(
            config["map_path"],
            config["room_template_directory"],
            config.get("generated_piece_count", 2),
        )
    elif config.get("map_path"):
        floor = load_tmx_floor(
            config["map_path"]
        )
    else:
        raise ValueError(
            "Act Three floor requires a TMX source"
        )

    attach_act_three_passages(
        floor,
        floor_index,
        floor_count,
    )
    floor["presentation_act"] = config.get("presentation_act", config["act"])

    return populate_act_three_enemies(
        floor,
        config["act_floor"],
    )
