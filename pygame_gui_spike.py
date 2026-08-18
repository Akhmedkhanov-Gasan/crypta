from pathlib import Path

import pygame
import pygame_gui


WINDOW_SIZE = (1280, 720)
ROOT = Path(__file__).resolve().parent
THEME_PATH = ROOT / "assets" / "ui" / "pygame_gui_spike_theme.json"


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("Crypta - pygame_gui spike")
    clock = pygame.time.Clock()
    manager = pygame_gui.UIManager(WINDOW_SIZE)
    manager.add_font_paths(
        "pixel_operator",
        str(ROOT / "assets" / "fonts" / "PixelOperator.ttf"),
        str(ROOT / "assets" / "fonts" / "PixelOperator-Bold.ttf"),
    )
    manager.get_theme().load_theme(str(THEME_PATH))

    hud_panel = pygame_gui.elements.UIPanel(
        pygame.Rect(24, 24, 390, 132),
        manager=manager,
        object_id="#hud_panel",
    )
    pygame_gui.elements.UILabel(
        pygame.Rect(18, 12, 220, 28),
        "ASSASSIN",
        manager=manager,
        container=hud_panel,
        object_id="#class_name",
    )
    level_label = pygame_gui.elements.UILabel(
        pygame.Rect(320, 12, 48, 28),
        "1",
        manager=manager,
        container=hud_panel,
        object_id="#level_label",
    )
    health_bar = pygame_gui.elements.UIProgressBar(
        pygame.Rect(18, 50, 350, 26),
        manager=manager,
        container=hud_panel,
        object_id="#health_bar",
    )
    health_bar.set_current_progress(68)
    experience_bar = pygame_gui.elements.UIProgressBar(
        pygame.Rect(18, 86, 350, 20),
        manager=manager,
        container=hud_panel,
        object_id="#experience_bar",
    )
    experience_bar.set_current_progress(35)

    rail_panel = pygame_gui.elements.UIPanel(
        pygame.Rect(1204, 188, 60, 344),
        manager=manager,
        object_id="#rail_panel",
    )
    rail_buttons = {}
    for index, (name, label) in enumerate(
        (
            ("inventory", "I"),
            ("stats", "S"),
            ("abilities", "A"),
            ("log", "L"),
            ("settings", "ESC"),
        )
    ):
        rail_buttons[name] = pygame_gui.elements.UIButton(
            pygame.Rect(6, 7 + index * 66, 48, 48),
            label,
            manager=manager,
            container=rail_panel,
            object_id=pygame_gui.core.ObjectID(
                class_id="@rail_button",
                object_id=f"#{name}_button",
            ),
            tool_tip_text=name.title(),
        )

    inventory_panel = pygame_gui.elements.UIPanel(
        pygame.Rect(850, 132, 330, 438),
        manager=manager,
        object_id="#inventory_panel",
    )
    inventory_title = pygame_gui.elements.UILabel(
        pygame.Rect(18, 14, 294, 34),
        "INVENTORY",
        manager=manager,
        container=inventory_panel,
        object_id="#window_title",
    )
    for slot_index in range(16):
        column = slot_index % 4
        row = slot_index // 4
        pygame_gui.elements.UIButton(
            pygame.Rect(20 + column * 73, 64 + row * 73, 62, 62),
            "",
            manager=manager,
            container=inventory_panel,
            object_id=pygame_gui.core.ObjectID(
                class_id="@inventory_slot",
                object_id=f"#slot_{slot_index}",
            ),
        )

    help_label = pygame_gui.elements.UILabel(
        pygame.Rect(24, 648, 660, 36),
        "Drag HP. Click I to toggle inventory. Resize the window to test the layout.",
        manager=manager,
        object_id="#help_label",
    )
    health_slider = pygame_gui.elements.UIHorizontalSlider(
        pygame.Rect(700, 650, 360, 30),
        68,
        (0, 100),
        manager=manager,
        object_id="#health_slider",
    )

    inventory_visible = True

    def update_layout(window_size):
        width, height = window_size
        rail_panel.set_relative_position((width - 76, max(24, (height - 344) // 2)))
        inventory_panel.set_relative_position(
            (max(440, width - 430), max(24, (height - 438) // 2))
        )
        help_label.set_relative_position((24, height - 72))
        health_slider.set_relative_position((max(500, width - 580), height - 70))

    update_layout(WINDOW_SIZE)
    running = True
    while running:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                new_size = (max(960, event.w), max(600, event.h))
                screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
                manager.set_window_resolution(new_size)
                update_layout(new_size)
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == rail_buttons["inventory"]:
                    inventory_visible = not inventory_visible
                    if inventory_visible:
                        inventory_panel.show()
                    else:
                        inventory_panel.hide()
                elif event.ui_element == rail_buttons["stats"]:
                    inventory_title.set_text("CHARACTER STATS")
                elif event.ui_element == rail_buttons["abilities"]:
                    inventory_title.set_text("ABILITIES")
                elif event.ui_element == rail_buttons["log"]:
                    inventory_title.set_text("EVENT LOG")
                elif event.ui_element == rail_buttons["settings"]:
                    inventory_title.set_text("SETTINGS")
            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == health_slider:
                    health_bar.set_current_progress(event.value)
                    level_label.set_text(str(1 + round(event.value / 10)))
            manager.process_events(event)

        manager.update(time_delta)
        screen.fill((6, 7, 10))
        width, height = screen.get_size()
        for y in range(0, height, 32):
            pygame.draw.line(screen, (18, 20, 24), (0, y), (width, y))
        for x in range(0, width, 64):
            pygame.draw.line(screen, (13, 15, 18), (x, 0), (x, height))
        manager.draw_ui(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
