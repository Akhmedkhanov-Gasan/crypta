from dataclasses import dataclass


@dataclass(frozen=True)
class TooltipContent:
    title: str
    lines: tuple[str, ...]
    accent: tuple[int, int, int]
    