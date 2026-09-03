import pygame

from presentation.display import game_viewport
from presentation.layout import ASSET_ROOT
from settings import FPS, GAME_HEIGHT, GAME_WIDTH


LOGO_DURATION_MS = 2500
SAND_DURATION_MS = 1600
TURN_DURATION_MS = 300
CYCLE_DURATION_MS = SAND_DURATION_MS + TURN_DURATION_MS
LOADING_DURATION_MS = CYCLE_DURATION_MS * 2

HOURGLASS_SCALE = 2
HOURGLASS_MARGIN = 32

_SKULL = (
    "...######...",
    "..########..",
    ".##########.",
    "############",
    "##...##...##",
    "##...##...##",
    ".##########.",
    "..###..###..",
    "...######...",
    "...#.##.#...",
    "....####....",
)

_TOP_GLASS = (
    (7, 7),
    (24, 7),
    (26, 11),
    (25, 15),
    (22, 19),
    (18, 23),
    (16, 25),
    (15, 25),
    (13, 23),
    (9, 19),
    (6, 15),
    (5, 11),
)

_BOTTOM_GLASS = tuple(
    (31 - x, 51 - y)
    for x, y in _TOP_GLASS
)




class StartupScreen:
    def __init__(self, window, fullscreen=False):
        self.window = window
        self.fullscreen = fullscreen
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.clock = pygame.time.Clock()
        self.elapsed_ms = 0

        self.window.fill((0, 0, 0))
        pygame.display.flip()

        self.skull = pygame.Surface((12, 11), pygame.SRCALPHA)
        for y, row in enumerate(_SKULL):
            for x, pixel in enumerate(row):
                if pixel == "#":
                    self.skull.set_at((x, y), (255, 255, 255))

        self.inverted_skull = pygame.transform.rotate(self.skull, 180)

        top_mask = pygame.Surface((32, 52), pygame.SRCALPHA)
        pygame.draw.polygon(top_mask, (255, 255, 255), _TOP_GLASS)
        pygame.draw.lines(
            top_mask,
            (0, 0, 0, 0),
            True,
            _TOP_GLASS,
            1,
        )

        self.top_pixels = [
            (x, y)
            for y in range(51, -1, -1)
            for x in range(32)
            if top_mask.get_at((x, y)).a
        ]

        self.bottom_pixels = sorted(
            (
                (31 - x, 51 - y)
                for x, y in self.top_pixels
            ),
            key=lambda point: (-point[1], point[0]),
        )

    def _events(self, allow_skip=False):
        skip = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if (
                event.type == pygame.VIDEORESIZE
                and not self.fullscreen
            ):
                self.window = pygame.display.set_mode(
                    (max(320, event.w), max(180, event.h)),
                    pygame.RESIZABLE,
                )

            if allow_skip:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    skip = True
                elif event.type == pygame.KEYDOWN:
                    if event.key in (
                        pygame.K_RETURN,
                        pygame.K_SPACE,
                        pygame.K_ESCAPE,
                    ):
                        skip = True

        return skip

    def _present(self, pixelated=False):
        viewport, _ = game_viewport(self.window.get_size())
        self.window.fill((0, 0, 0))

        if viewport.size == self.surface.get_size():
            image = self.surface
        elif pixelated:
            image = pygame.transform.scale(
                self.surface,
                viewport.size,
            )
        else:
            image = pygame.transform.smoothscale(
                self.surface,
                viewport.size,
            )

        self.window.blit(image, viewport)
        pygame.display.flip()

    def show_logo(self):
        path = ASSET_ROOT / "ui" / "menu" / "nihil.png"
        logo = pygame.image.load(str(path)).convert_alpha()

        scale = min(
            GAME_WIDTH * 0.55 / logo.get_width(),
            GAME_HEIGHT * 0.68 / logo.get_height(),
        )
        logo = pygame.transform.smoothscale(
            logo,
            (
                max(1, round(logo.get_width() * scale)),
                max(1, round(logo.get_height() * scale)),
            ),
        )
        rectangle = logo.get_rect(
            center=(GAME_WIDTH // 2, GAME_HEIGHT // 2),
        )
        started_at = pygame.time.get_ticks()

        while True:
            self.clock.tick(FPS)

            if self._events(allow_skip=True):
                break

            elapsed = pygame.time.get_ticks() - started_at
            if elapsed >= LOGO_DURATION_MS:
                break

            opacity = max(
                0.0,
                min(
                    1.0,
                    elapsed / 350,
                    (LOGO_DURATION_MS - elapsed) / 450,
                ),
            )

            logo.set_alpha(round(255 * opacity))
            self.surface.fill((0, 0, 0))
            self.surface.blit(logo, rectangle)
            self._present()

        self.clock.tick()
        self._frame()

    def _hourglass(self):
        cycle_time = self.elapsed_ms % CYCLE_DURATION_MS
        progress = min(1.0, cycle_time / SAND_DURATION_MS)

        image = pygame.Surface((32, 52), pygame.SRCALPHA)

        for polygon in (_TOP_GLASS, _BOTTOM_GLASS):
            pygame.draw.polygon(image, (0, 0, 0), polygon)

        image.blit(self.skull, (10, 9))
        image.blit(self.inverted_skull, (10, 32))

        if 0.0 < progress < 1.0:
            offset = int(cycle_time / 65)
            for y in range(25, 45):
                if (y + offset) % 4 != 0:
                    x = 15 + ((y + offset) % 2)
                    image.set_at((x, y), (255, 255, 255))

        top_count = round(len(self.top_pixels) * (1.0 - progress))
        bottom_count = len(self.bottom_pixels) - top_count

        for pixels, count in (
                (self.top_pixels, top_count),
                (self.bottom_pixels, bottom_count),
        ):
            for x, y in pixels[:count]:
                shade = (
                    220
                    if (x * 7 + y * 13) % 23 == 0
                    else 255
                )
                image.set_at((x, y), (shade, shade, shade))

        for polygon in (_TOP_GLASS, _BOTTOM_GLASS):
            pygame.draw.lines(
                image,
                (145, 145, 145),
                True,
                polygon,
                1,
            )

        for start, end in (
                ((8, 7), (23, 7)),
                ((6, 10), (6, 12)),
                ((7, 14), (8, 16)),
        ):
            pygame.draw.line(image, (245, 245, 245), start, end)
            pygame.draw.line(
                image,
                (245, 245, 245),
                (31 - start[0], 51 - start[1]),
                (31 - end[0], 51 - end[1]),
            )

        for x in (3, 27):
            pygame.draw.rect(
                image,
                (65, 65, 65),
                (x, 6, 2, 40),
            )

        pygame.draw.line(
            image,
            (115, 115, 115),
            (3, 7),
            (3, 44),
        )
        pygame.draw.line(
            image,
            (115, 115, 115),
            (28, 7),
            (28, 44),
        )

        for y, left, right, shade in (
                (2, 8, 23, 125),
                (3, 5, 26, 165),
                (4, 2, 29, 100),
                (5, 3, 28, 55),
        ):
            color = (shade, shade, shade)
            pygame.draw.line(
                image,
                color,
                (left, y),
                (right, y),
            )
            pygame.draw.line(
                image,
                color,
                (left, 51 - y),
                (right, 51 - y),
            )

        if cycle_time > SAND_DURATION_MS:
            turn = (cycle_time - SAND_DURATION_MS) / TURN_DURATION_MS
            turn = turn * turn * (3.0 - 2.0 * turn)
            image = pygame.transform.rotate(image, -180.0 * turn)

        return pygame.transform.scale(
            image,
            (
                image.get_width() * HOURGLASS_SCALE,
                image.get_height() * HOURGLASS_SCALE,
            ),
        )

    def _frame(self):
        self.elapsed_ms += min(self.clock.tick(FPS), 50)
        self._events()
        self.surface.fill((0, 0, 0))

        image = self._hourglass()
        center = (
            GAME_WIDTH - HOURGLASS_MARGIN - 16 * HOURGLASS_SCALE,
            GAME_HEIGHT - HOURGLASS_MARGIN - 26 * HOURGLASS_SCALE,
        )
        self.surface.blit(image, image.get_rect(center=center))
        self._present(pixelated=True)

    def load(self, loader, *args, **kwargs):
        self._frame()
        result = loader(*args, **kwargs)
        self.clock.tick()
        self._frame()
        return result

    def finish(self):
        while self.elapsed_ms < LOADING_DURATION_MS:
            self._frame()

        self.surface.fill((0, 0, 0))
        self._present()