from settings import TEXT_COLOR


LOG_EVENT_COLORS = {
    "neutral": TEXT_COLOR,
    "player_attack": (191, 154, 91),
    "enemy_attack": (181, 82, 82),
    "critical": (214, 171, 87),
    "defense": (105, 139, 158),
    "death": (174, 66, 75),
    "progress": (157, 143, 101),
    "healing": (111, 161, 121),
    "enemy_healing": (151, 132, 84),
    "buff": (119, 157, 128),
    "debuff": (160, 94, 113),
    "loot": (126, 158, 123),
    "trade": (181, 132, 84),
    "dialogue": (158, 132, 174),
    "quest": (133, 119, 169),
    "ability": (102, 141, 169),
    "rune": (135, 108, 174),
    "altar": (155, 79, 96),
    "environment": (132, 143, 145),
    "warning": (190, 120, 74),
    "system": (141, 136, 128),
}


def get_event_color(message):
    category = getattr(message, "category", "neutral")
    return LOG_EVENT_COLORS.get(category, LOG_EVENT_COLORS["neutral"])


def fit_text_to_width(font, text, maximum_width):
    if font.size(text)[0] <= maximum_width:
        return text

    ellipsis = "..."
    shortened_text = text

    while (
        shortened_text
        and font.size(shortened_text + ellipsis)[0] > maximum_width
    ):
        shortened_text = shortened_text[:-1]

    return shortened_text.rstrip() + ellipsis


def wrap_text(font, text, maximum_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        candidate = f"{current_line} {word}" if current_line else word

        if font.size(candidate)[0] <= maximum_width:
            current_line = candidate
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines
