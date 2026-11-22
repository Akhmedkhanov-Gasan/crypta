from dataclasses import dataclass, field


@dataclass(frozen=True)
class RuneCard:
    id: str
    slot: str
    name: str
    description: str
    icon_paths: tuple[str, ...] = ()
    placeholder: bool = False


@dataclass
class RuneMenuState:
    abilities: tuple[RuneCard, ...] = ()
    choices: tuple[RuneCard, ...] = ()
    page: str = "abilities"
    phase: str = "opening"
    started_at: int = 0
    opened_at: int = 0
    selected_ability: int = 0
    selected_choice: int | None = None
    previous_choice: int | None = None
    selection_started_at: int = 0
    focus: int = 0
    keyboard_focus: bool = False
    pressed: str | None = None
    pending_button_action: str | None = None
    pending_button_started_at: int = 0
    pending_page: str = "abilities"
    confirming_choice: bool = False
