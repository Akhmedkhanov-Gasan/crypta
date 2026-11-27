from acts.act_three.rune_master.motion import card_hitbox, card_poses
from presentation.figma_ui import figma_rect


def motion_layout(layout):
    return {**layout, "slots_container": layout["pact_container"],
            "slots": {f"slot_{index:02d}": layout["pacts"][f"pact_{index:02d}"] for index in range(1, 4)}}


def poses(menu, layout, current_time):
    return card_poses(menu, motion_layout(layout), current_time)


def hitbox(layout, pose):
    rectangle = card_hitbox(motion_layout(layout), pose)
    spec = layout["pacts"][f"pact_{pose.index + 1:02d}"]
    bounds = figma_rect(spec["rect"])
    rarity = figma_rect(spec["rarity"]).move(pose.rect.x - bounds.x, pose.rect.y - bounds.y)
    return rectangle.union(rarity)
