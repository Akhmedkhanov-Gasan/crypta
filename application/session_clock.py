import pygame


_real_get_ticks = pygame.time.get_ticks
_offset = 0


def _get_session_ticks():
    return _real_get_ticks() + _offset


def restore_session_time(saved_ticks):
    global _offset

    if type(saved_ticks) is not int or saved_ticks < 0:
        raise ValueError("Invalid saved session time.")

    _offset = saved_ticks - _real_get_ticks()
    pygame.time.get_ticks = _get_session_ticks
    