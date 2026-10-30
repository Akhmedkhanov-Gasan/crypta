FAREWELL_LINES = (
    ("OLD MAN", "Even now... he thought he could keep the dark from you."),
    ("OLD MAN", "There is no kindness in what remains. Only another veil."),
    ("OLD MAN", "You must see more clearly now. Even what you would rather leave unseen."),
    ("YOU", "Wait! Explain--"),
)

ARRIVAL_LINES = (
    ("OLD MAN", "You have come far. Further than he believed you would."),
    ("OLD MAN", "The world has shown you another face. Now show it yours."),
    ("OLD MAN", "Tell me... who are you, beneath all that you have become?"),
)

SUBCLASS_LINES = {
    "assassin": (
        "You knew what I would become. What else are you hiding?",
        "Gone. But not without a reason.",
    ),
    "archer": (
        "You keep pointing me forward. What are you keeping out of sight?",
        "Fine. Every trail ends somewhere.",
    ),
    "berserker": (
        "Will you explain what the fuck is happening here already?",
        "Of course. Fucking disappear. I'll find my own answers.",
    ),
    "paladin": (
        "You ask me to choose a path. By what oath do you guide mine?",
        "Then let my deeds answer where your words will not.",
    ),
    "warlock": (
        "Power always has a price. Tell me who is collecting yours.",
        "Keep your secrets, old man. Nothing stays buried forever.",
    ),
    "summoner": (
        "It knows this place. What have you bound us to?",
        "At least you are still here. Come. We will find out together.",
    ),
}

TRANSFORM_MS = 2600
BLACKOUT_MS = 2800
APPEAR_MS = 1400
TURN_START_MS = 1900
TURN_END_MS = 2500
ARRIVAL_DIALOGUE_MS = 3800


def line_duration(text):
    return max(2800, len(text) * 34 + 1700)


def dialogue_timeline(lines, start):
    timeline = []
    for speaker, text in lines:
        end = start + line_duration(text)
        timeline.append((start, end, speaker, text))
        start = end + 400
    return tuple(timeline)


FAREWELL = dialogue_timeline(FAREWELL_LINES, 2900)
ARRIVAL = dialogue_timeline(ARRIVAL_LINES, ARRIVAL_DIALOGUE_MS)
FAREWELL_END_MS = FAREWELL[-1][0] + 620
ARRIVAL_END_MS = ARRIVAL[-1][1] + 500


def answer_timeline(subclass):
    first, last = SUBCLASS_LINES[subclass]
    first_end = 650 + line_duration(first)
    last_start = first_end + 2200
    return (
        (650, first_end, subclass.upper(), first),
        (last_start, last_start + line_duration(last), subclass.upper(), last),
    )

