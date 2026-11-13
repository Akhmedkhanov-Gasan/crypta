import pygame

from presentation.figma_ui import draw_figma_rectangle, figma_rect


def draw_panel_image(screen, assets, name, rectangle, alpha=255):
    if rectangle is None:
        return

    image = assets.get(f"hud_panel_{name}")
    if image is None:
        return

    target = figma_rect(rectangle)
    image = pygame.transform.smoothscale(image, target.size)
    if alpha != 255:
        image.set_alpha(alpha)
    screen.blit(image, target)


def draw_panel_row_background(screen, row):
    background = row.get("background")
    if background is not None:
        draw_figma_rectangle(screen, background)


def draw_panel_rank_track(screen, assets, track, current_rank):
    kind = track.get("kind", "mastery")
    draw_panel_image(screen, assets, f"frame_{kind}", track.get("frame"))
    current_rank = max(0, min(5, int(current_rank)))

    for index, name in enumerate(sorted(track["levels"]), start=1):
        draw_panel_image(
            screen,
            assets,
            f"level_{kind}",
            track["levels"][name],
            255 if index <= current_rank else 65,
        )


def draw_panel_equipment(screen, assets, equipment):
    draw_panel_image(screen, assets, "equipment_decoration", equipment.get("decoration"))
    for name, item in (("weapon", "sword"), ("armor", "armor")):
        track = equipment[name]
        draw_panel_image(screen, assets, "icon", track.get("icon"))
        draw_panel_image(screen, assets, item, track.get("item_icon"))
