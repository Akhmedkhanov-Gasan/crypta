import pygame

from game.dev_commands import (
    CONSOLE_HELP,
    execute_console_command,
)


class DevConsole:
    def __init__(self):
        self.is_open = False
        self.input_text = ""
        self.lines = ["Type help to list commands."]
        self.history = []
        self.history_index = 0
        self.history_draft = ""
        self.font = pygame.font.SysFont("consolas", 20)

    def open(self):
        self.is_open = True
        self.history_index = len(self.history)
        self.history_draft = self.input_text
        pygame.key.start_text_input()

    def close(self):
        if not self.is_open:
            return

        self.is_open = False
        pygame.key.stop_text_input()

    def write(self, text):
        self.lines.extend(str(text).splitlines())
        self.lines = self.lines[-100:]

    def submit(self, game_state):
        command = self.input_text.strip()
        self.input_text = ""
        self.history_draft = ""

        if not command:
            self.history_index = len(self.history)
            return

        self.history.append(command)
        self.history = self.history[-100:]
        self.history_index = len(self.history)
        self.write(f"> {command}")

        if command.lower() == "help":
            for line in CONSOLE_HELP:
                self.write(line)
        elif command.lower() == "clear":
            self.lines.clear()
        else:
            result = execute_console_command(
                game_state,
                command,
                self.close,
            )
            if result:
                self.write(result)

    def handle_event(self, event, game_state):
        if not self.is_open:
            return False

        if event.type in (
            pygame.QUIT,
            pygame.VIDEORESIZE,
            pygame.WINDOWFOCUSLOST,
        ):
            return False

        if event.type == pygame.TEXTINPUT:
            text = "".join(
                character
                for character in event.text
                if character.isprintable()
                and character not in "`~ёЁ"
            )
            self.input_text = (self.input_text + text)[:200]
            self.history_index = len(self.history)
            self.history_draft = self.input_text

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()


            elif event.key in (
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER,
            ):
                self.submit(game_state)

            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                self.history_index = len(self.history)
                self.history_draft = self.input_text

            elif event.key == pygame.K_UP and self.history:
                if self.history_index == len(self.history):
                    self.history_draft = self.input_text

                self.history_index = max(
                    0,
                    self.history_index - 1,
                )
                self.input_text = self.history[self.history_index]

            elif event.key == pygame.K_DOWN and self.history:
                self.history_index = min(
                    len(self.history),
                    self.history_index + 1,
                )
                self.input_text = (
                    self.history_draft
                    if self.history_index == len(self.history)
                    else self.history[self.history_index]
                )

        return True

    def draw(self, surface):
        if not self.is_open:
            return

        width = surface.get_width()
        height = min(320, surface.get_height())
        panel = pygame.Surface(
            (width, height),
            pygame.SRCALPHA,
        )
        panel.fill((12, 14, 20, 240))

        pygame.draw.line(
            panel,
            (100, 115, 140),
            (0, height - 1),
            (width, height - 1),
        )

        panel.blit(
            self.font.render(
                "DEV CONSOLE",
                True,
                (225, 195, 130),
            ),
            (16, 12),
        )

        line_height = self.font.get_linesize()
        input_y = height - line_height - 16
        visible_count = max(
            1,
            (input_y - 60) // line_height,
        )

        panel.set_clip(
            pygame.Rect(16, 44, width - 32, input_y - 52)
        )

        for index, line in enumerate(
            self.lines[-visible_count:]
        ):
            panel.blit(
                self.font.render(
                    line,
                    True,
                    (210, 215, 225),
                ),
                (16, 44 + index * line_height),
            )

        panel.set_clip(None)

        pygame.draw.line(
            panel,
            (60, 70, 90),
            (16, input_y - 8),
            (width - 16, input_y - 8),
        )

        visible_input = self.input_text
        while (
            visible_input
            and self.font.size(f"> {visible_input}_")[0]
            > width - 32
        ):
            visible_input = visible_input[1:]

        cursor = (
            "_"
            if pygame.time.get_ticks() // 500 % 2 == 0
            else " "
        )

        panel.blit(
            self.font.render(
                f"> {visible_input}{cursor}",
                True,
                (245, 245, 245),
            ),
            (16, input_y),
        )

        surface.blit(panel, (0, 0))
