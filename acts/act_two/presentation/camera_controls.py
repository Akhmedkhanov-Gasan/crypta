import resource_store as resources

from presentation.map_navigation import CameraControls


def create_act_two_camera_controls(hud_layout):
    directory = "assets/sprites/ui/act_2/camera"

    images = {
        name: resources.load_image(
            f"{directory}/{filename}"
        ).convert_alpha()
        for name, filename in (
            ("normal", "normal.png"),
            ("overview", "overview.png"),
            ("buttons", "image.png"),
        )
    }

    font = resources.load_font(
        "assets/fonts/alagard/alagard.ttf",
        16,
    )

    return CameraControls(
        hud_layout["down_bar"]["camera"],
        images,
        font,
    )
