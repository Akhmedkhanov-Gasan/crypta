import pygame

from acts.act_three.presentation.hud.assets import _ART_RECTS
from acts.act_three.presentation.hud.layout import get_layout_rect
from acts.act_three.presentation.hud.renderer import draw_act_three_hud
from presentation.display import game_viewport, present_game
from settings import GAME_HEIGHT, GAME_WIDTH


_PIXEL_FIELDS = frozenset({
    "x", "y", "width", "height", "size", "corner_radius",
    "stroke_weight", "blur_radius",
})


def _scale_layout(value, scale):
    if isinstance(value, list):
        return [_scale_layout(item, scale) for item in value]
    if not isinstance(value, dict):
        return value

    result = {}
    for key, item in value.items():
        if (
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and (
                key in _PIXEL_FIELDS
                or (key == "value" and value.get("unit") == "PIXELS")
            )
        ):
            result[key] = round(item * scale)
        else:
            result[key] = _scale_layout(item, scale)
    return result


class NativeActThreeHud:
    def __init__(self):
        self._cache_key = None
        self._assets = None
        self._foreground = None

    def foreground(self, size):
        if self._foreground is None or self._foreground.get_size() != size:
            self._foreground = pygame.Surface(size, pygame.SRCALPHA)
        self._foreground.fill((0, 0, 0, 0))
        return self._foreground

    def _prepare_assets(self, assets, size):
        key = (id(assets), size)
        if key == self._cache_key:
            return self._assets

        scale = min(size[0] / GAME_WIDTH, size[1] / GAME_HEIGHT)
        layout = _scale_layout(assets["act_three_hud_layout"], scale)
        prepared = dict(assets)
        prepared["act_three_hud_layout"] = layout
        prepared["hud_render_scale"] = scale

        for name, source in assets["hud_source_images"].items():
            rectangle = get_layout_rect(layout, *_ART_RECTS[name])
            prepared[name] = pygame.transform.smoothscale(source, rectangle.size)

        portrait_rect = get_layout_rect(layout, "top_bar", "portrait")
        prepared["hud_portraits"] = {
            name: pygame.transform.smoothscale(source, portrait_rect.size)
            for name, source in assets["hud_portrait_sources"].items()
        }
        prepared["hud_candle_flames"] = {
            name: tuple(
                pygame.transform.smoothscale(
                    source,
                    get_layout_rect(layout, "top_bar", "candles", name).size,
                )
                for source in sources
            )
            for name, sources in assets["hud_candle_sources"].items()
        }
        self._assets = prepared
        self._cache_key = key
        return prepared

    def present(self, window, game_surface, foreground, game_state, fonts, assets, current_time):
        present_game(window, game_surface, flip=False)
        viewport, _ = game_viewport(window.get_size())
        target = window.subsurface(viewport)

        if not game_state.act_three_transition_open:
            prepared = self._prepare_assets(assets, viewport.size)
            mouse = pygame.mouse.get_pos()
            mouse_position = (
                (mouse[0] - viewport.x, mouse[1] - viewport.y)
                if viewport.collidepoint(mouse) else None
            )
            draw_act_three_hud(
                target, game_state, fonts, prepared, current_time, mouse_position,
            )

        if foreground.get_size() == target.get_size():
            target.blit(foreground, (0, 0))
        else:
            target.blit(pygame.transform.smoothscale(foreground, target.get_size()), (0, 0))

        pygame.transform.smoothscale(target, game_surface.get_size(), game_surface)
        pygame.display.flip()
