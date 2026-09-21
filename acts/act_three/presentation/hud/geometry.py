from acts.act_three.presentation.hud.layout import (
    get_act_three_hud_layout,
    get_layout_rect,
)


def get_act_three_sidebar_tab_rectangles():
    layout = get_act_three_hud_layout()
    buttons = layout["right_bar"]["tabs"]["buttons"]

    return {
        name: get_layout_rect(
            layout,
            "right_bar",
            "tabs",
            "buttons",
            name,
            "hitbox",
        )
        for name in buttons
    }


def get_act_three_panel_close_rectangle(panel_name):
    layout = get_act_three_hud_layout()

    if panel_name == "journal":
        return get_layout_rect(
            layout,
            "journal_panel",
            "close_hitbox",
        )

    return get_layout_rect(
        layout,
        "right_bar",
        "character_panel",
        "close_hitbox",
    )


def get_act_three_popup_rectangle(panel_name):
    layout = get_act_three_hud_layout()

    if panel_name == "journal":
        return get_layout_rect(
            layout,
            "journal_panel",
        )

    return get_layout_rect(
        layout,
        "right_bar",
        "character_panel",
    )


def get_act_three_attribute_button_rectangles():
    layout = get_act_three_hud_layout()
    rows = layout[
        "right_bar"
    ][
        "character_panel"
    ][
        "attributes"
    ][
        "rows"
    ]

    return {
        name: {
            "minus": get_layout_rect(
                layout,
                "right_bar",
                "character_panel",
                "attributes",
                "rows",
                name,
                "minus_hitbox",
            ),
            "plus": get_layout_rect(
                layout,
                "right_bar",
                "character_panel",
                "attributes",
                "rows",
                name,
                "plus_hitbox",
            ),
        }
        for name in rows
    }


def get_act_three_character_confirm_rectangle():
    return get_layout_rect(
        get_act_three_hud_layout(),
        "right_bar",
        "character_panel",
        "confirm",
        "hitbox",
    )


def get_act_three_bottom_hud_rectangles():
    layout = get_act_three_hud_layout()

    return (
        get_layout_rect(
            layout,
            "top_bar",
            "frame",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "combat_log",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "consumable_belt_frame",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "abilities",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "gold",
        ),
        get_layout_rect(
            layout,
            "down_bar",
            "camera",
        ),
    )


def get_act_three_log_panel_rect():
    layout = get_act_three_hud_layout()

    return get_layout_rect(
        layout,
        "down_bar",
        "combat_log",
    )


def get_act_three_log_arrow_rectangles():
    return {}
