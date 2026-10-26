AWAKENING_OPEN_START_MS = 300
AWAKENING_OPEN_END_MS = 1400
AWAKENING_HOLD_END_MS = 2000
AWAKENING_FADE_END_MS = 2800
AWAKENING_SECOND_OPEN_START_MS = 3300
AWAKENING_SECOND_OPEN_END_MS = 4700
AWAKENING_RECOVERY_BLINK_START_MS = 5750
AWAKENING_RECOVERY_BLINK_END_MS = 7950
AWAKENING_OLD_MAN_APPROACH_START_MS = 4700
AWAKENING_OLD_MAN_APPROACH_END_MS = 7700
AWAKENING_DIALOGUE_START_MS = 7700

AWAKENING_VOICE_START_MS = 1200
AWAKENING_BLACKOUT_START_MS = 10600
AWAKENING_WORLD_SWAP_MS = 11400
AWAKENING_BLACKOUT_END_MS = 12800
AWAKENING_OLD_MAN_DIALOGUE_START_MS = 13600

CLASS_SELECTION_READY_MS = 26800
CLASS_SELECTION_TRANSFORM_END_MS = 1200
CLASS_SELECTION_TURN_TO_OLD_MAN_MS = 1700

CLASS_SELECTION_DIALOGUE_LINES = {
    "warrior": (
        "So you chose the path of the warrior?",
        "Good. Then endure what waits above.",
    ),
    "rogue": (
        "So you chose the path of the rogue?",
        "Good. Then let the dark lose sight of you.",
    ),
    "mage": (
        "So you chose the path of the mage?",
        "Good. Then learn which truths must remain buried.",
    ),
}

CLASS_SELECTION_DIALOGUE_START_MS = 1900
CLASS_SELECTION_DIALOGUE_GAP_MS = 350


def class_selection_line_duration(line):
    return max(
        3000,
        len(line) * 34 + 1900,
        len(line.split()) * 340 + 800,
    )


def class_selection_dialogue_timing(selected_class):
    first_line, second_line = CLASS_SELECTION_DIALOGUE_LINES[
        selected_class
    ]
    first_start = CLASS_SELECTION_DIALOGUE_START_MS
    first_end = (
        first_start
        + class_selection_line_duration(first_line)
    )
    second_start = (
        first_end
        + CLASS_SELECTION_DIALOGUE_GAP_MS
    )
    second_end = (
        second_start
        + class_selection_line_duration(second_line)
    )

    return (
        (
            first_start,
            first_end,
            first_line,
        ),
        (
            second_start,
            second_end,
            second_line,
        ),
    )


_CLASS_SELECTION_DIALOGUE_END_MS = max(
    class_selection_dialogue_timing(
        selected_class,
    )[-1][1]
    for selected_class in CLASS_SELECTION_DIALOGUE_LINES
)

CLASS_SELECTION_OLD_MAN_FADE_START_MS = (
    _CLASS_SELECTION_DIALOGUE_END_MS + 450
)
CLASS_SELECTION_OLD_MAN_FADE_END_MS = (
    CLASS_SELECTION_OLD_MAN_FADE_START_MS + 1400
)
CLASS_SELECTION_WALK_START_MS = (
    CLASS_SELECTION_OLD_MAN_FADE_END_MS + 400
)
CLASS_SELECTION_WALK_END_MS = (
    CLASS_SELECTION_WALK_START_MS + 2700
)
CLASS_SELECTION_CHOICE_END_MS = (
    CLASS_SELECTION_WALK_END_MS + 700
)
