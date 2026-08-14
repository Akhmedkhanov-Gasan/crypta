import pytest

from game.events import GameEvent, GameEventType
from game.factories import create_game_state
from game.state import ChestState
from presentation.audio import (
    ActOneSoundBank,
    ActTwoSoundBank,
    ActTwoTransitionSoundBank,
    sound_keys_for_act_one_events,
    warden_has_been_defeated,
    warden_music_should_play,
)
from systems.player_actions import open_chest


def test_act_one_combat_events_become_sound_layers():
    events = [
        GameEvent(type=GameEventType.ATTACK, actor="hero"),
        GameEvent(type=GameEventType.HIT, actor="hero", target="Goblin 1"),
        GameEvent(
            type=GameEventType.PREPARE_ATTACK,
            actor="Brute 1",
            data={"enemy_type": "brute"},
        ),
    ]

    assert sound_keys_for_act_one_events(events) == [
        "sword_impact",
        "enemy_pain",
    ]


def test_act_one_pickups_and_healing_have_distinct_sounds():
    events = [
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            data={"kind": "potion"},
        ),
        GameEvent(
            type=GameEventType.HEAL,
            actor="hero",
            target="hero",
        ),
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            data={"kind": "gold"},
        ),
        GameEvent(type=GameEventType.CHEST_OPEN, actor="hero"),
    ]

    assert sound_keys_for_act_one_events(events) == [
        "potion_pickup",
        "healing",
        "gold_pickup",
        "chest_open",
    ]


def test_warden_uses_boss_warning_and_attack_sounds():
    events = [
        GameEvent(
            type=GameEventType.PREPARE_ATTACK,
            actor="Crypt Warden",
            data={"enemy_type": "warden"},
        ),
        GameEvent(type=GameEventType.ATTACK, actor="Crypt Warden"),
    ]

    assert sound_keys_for_act_one_events(events) == [
        "warden_warning",
        "warden_attack",
    ]


def test_common_enemy_attack_sound_plays_only_on_hit():
    missed_attack = [
        GameEvent(type=GameEventType.ATTACK, actor="Goblin 1"),
    ]
    successful_attack = [
        GameEvent(type=GameEventType.ATTACK, actor="Goblin 1"),
        GameEvent(
            type=GameEventType.HIT,
            actor="Goblin 1",
            target="hero",
        ),
    ]

    assert sound_keys_for_act_one_events(missed_attack) == []
    assert sound_keys_for_act_one_events(successful_attack) == [
        "common_enemy_attack",
    ]


def test_regular_enemy_preparation_is_silent():
    events = [
        GameEvent(
            type=GameEventType.PREPARE_ATTACK,
            actor="Goblin 1",
            data={"enemy_type": "goblin"},
        ),
    ]

    assert sound_keys_for_act_one_events(events) == []


def test_defeated_enemy_uses_death_instead_of_pain_sound():
    events = [
        GameEvent(
            type=GameEventType.HIT,
            actor="hero",
            target="Goblin 1",
        ),
        GameEvent(type=GameEventType.DEATH, actor="Goblin 1"),
    ]

    assert sound_keys_for_act_one_events(events) == [
        "sword_impact",
        "enemy_death",
    ]


def test_chest_sound_event_requires_successful_opening():
    game_state = create_game_state()
    chest = ChestState(1, 1, "gold")

    open_chest(game_state, chest)
    assert not any(
        event.type is GameEventType.CHEST_OPEN
        for event in game_state.events
    )

    game_state.player.key_count = 1
    open_chest(game_state, chest)
    assert any(
        event.type is GameEventType.CHEST_OPEN
        for event in game_state.events
    )


def test_sound_bank_master_volume_scales_each_effect():
    class FakeSound:
        def __init__(self):
            self.volume = None

        def set_volume(self, volume):
            self.volume = volume

    sound = FakeSound()
    sound_bank = ActOneSoundBank({"sword_impact": [sound]})

    sound_bank.set_master_volume(0.5)

    assert sound_bank.master_volume == 0.5
    assert sound.volume == 0.35


def test_warden_music_waits_for_actual_warden_fight():
    regular_floor = create_game_state(floor_index=0).floor
    warden_floor = create_game_state(floor_index=2).floor

    assert regular_floor.boss_fight_started
    assert not warden_music_should_play(regular_floor)
    assert not warden_music_should_play(warden_floor)

    warden_floor.boss_fight_started = True

    assert warden_music_should_play(warden_floor)


def test_warden_music_fades_only_after_warden_dies():
    warden_floor = create_game_state(floor_index=2).floor

    assert not warden_has_been_defeated(warden_floor)

    for enemy in warden_floor.enemies:
        if enemy.type == "warden":
            enemy.health = 0

    assert warden_has_been_defeated(warden_floor)


def test_act_two_transition_sound_volume_is_shared():
    class FakeSound:
        def __init__(self):
            self.volume = None

        def set_volume(self, volume):
            self.volume = volume

    sounds = {
        "eyes_close": FakeSound(),
        "eyes_open": FakeSound(),
        "class_select": FakeSound(),
    }
    sound_bank = ActTwoTransitionSoundBank(sounds)

    sound_bank.set_master_volume(0.4)

    assert sounds["eyes_close"].volume == pytest.approx(0.54)
    assert sounds["eyes_open"].volume == pytest.approx(0.54)
    assert sounds["class_select"].volume == 0.4


def test_act_two_warrior_death_replaces_hurt_sound():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    hurt = FakeSound()
    death = FakeSound()
    sound_bank = ActTwoSoundBank(
        {"warrior_hurt": [hurt], "warrior_death": [death]}
    )
    events = [
        GameEvent(type=GameEventType.HIT, actor="Goblin 1", target="hero"),
        GameEvent(type=GameEventType.DEATH, actor="hero"),
    ]

    sound_bank.play_events(events, "warrior")

    assert hurt.play_count == 0
    assert death.play_count == 1


def test_act_two_basic_warrior_attack_only_sounds_on_enemy_hit():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    impact = FakeSound()
    sound_bank = ActTwoSoundBank({"warrior_hit": [impact]})
    attack = GameEvent(
        type=GameEventType.ATTACK,
        actor="hero",
        data={"kind": "basic"},
    )

    sound_bank.play_events([attack], "warrior")
    assert impact.play_count == 0

    sound_bank.play_events(
        [
            attack,
            GameEvent(
                type=GameEventType.HIT,
                actor="hero",
                target="Goblin 1",
            ),
        ],
        "warrior",
    )
    assert impact.play_count == 1


def test_act_two_environment_events_play_their_matching_sounds():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    sounds = {
        sound_key: [FakeSound()]
        for sound_key in (
            "rune_activate",
            "chest_open",
            "gold_pickup",
            "item_pickup",
            "key_pickup",
            "rogue_hit",
            "chest_break",
        )
    }
    sound_bank = ActTwoSoundBank(sounds)
    events = [
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            data={"kind": "wall_rune", "activated": True},
        ),
        GameEvent(type=GameEventType.CHEST_OPEN, actor="hero"),
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            data={"kind": "gold"},
        ),
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            data={"kind": "key"},
        ),
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            data={"kind": "potion"},
        ),
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            data={"kind": "breakable_crate"},
        ),
    ]

    sound_bank.play_events(events, "rogue")

    assert all(variants[0].play_count == 1 for variants in sounds.values())


def test_act_two_repeat_rune_interaction_is_silent():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    rune_sound = FakeSound()
    sound_bank = ActTwoSoundBank({"rune_activate": [rune_sound]})
    event = GameEvent(
        type=GameEventType.ATTACK,
        actor="hero",
        data={"kind": "wall_rune", "activated": False},
    )

    sound_bank.play_events([event], "warrior")

    assert rune_sound.play_count == 0


def test_act_two_rogue_sounds_cover_combat_and_invisibility():
    class FakeChannel:
        def __init__(self):
            self.volume = None

        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.channels = []

        def play(self):
            channel = FakeChannel()
            self.channels.append(channel)
            return channel

    hit = FakeSound()
    invisibility = FakeSound()
    hurt = FakeSound()
    sound_bank = ActTwoSoundBank(
        {
            "rogue_hit": [hit],
            "rogue_invisibility": [invisibility],
            "rogue_hurt": [hurt],
        }
    )
    events = [
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            data={"kind": "basic"},
        ),
        GameEvent(
            type=GameEventType.HIT,
            actor="hero",
            target="Goblin 1",
            data={"critical": True, "blocked": False},
        ),
        GameEvent(
            type=GameEventType.ABILITY,
            actor="hero",
            data={"ability": "invisibility"},
        ),
        GameEvent(type=GameEventType.HIT, actor="Goblin 1", target="hero"),
    ]

    sound_bank.play_events(events, "rogue")

    assert len(hit.channels) == 1
    assert hit.channels[0].volume == pytest.approx(0.78 * 1.2)
    assert len(invisibility.channels) == 1
    assert len(hurt.channels) == 1


def test_act_two_rogue_death_replaces_hurt_sound():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    hurt = FakeSound()
    death = FakeSound()
    sound_bank = ActTwoSoundBank(
        {"rogue_hurt": [hurt], "rogue_death": [death]}
    )
    events = [
        GameEvent(type=GameEventType.HIT, actor="Goblin 1", target="hero"),
        GameEvent(type=GameEventType.DEATH, actor="hero"),
    ]

    sound_bank.play_events(events, "rogue")

    assert hurt.play_count == 0
    assert death.play_count == 1


def test_act_two_mage_sounds_cover_attack_ability_hurt_and_death():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    hit = FakeSound()
    burst = FakeSound()
    hurt = FakeSound()
    death = FakeSound()
    sound_bank = ActTwoSoundBank(
        {
            "mage_hit": [hit],
            "mage_arcane_burst": [burst],
            "mage_hurt": [hurt],
            "mage_death": [death],
        }
    )

    sound_bank.play_events(
        [
            GameEvent(
                type=GameEventType.ATTACK,
                actor="hero",
                data={"kind": "basic"},
            ),
            GameEvent(
                type=GameEventType.HIT,
                actor="hero",
                target="Goblin 1",
                data={"blocked": False},
            ),
        ],
        "mage",
    )
    sound_bank.play_events(
        [
            GameEvent(
                type=GameEventType.ATTACK,
                actor="hero",
                data={"kind": "ability", "ability": "arcane burst"},
            )
        ],
        "mage",
    )
    sound_bank.play_events(
        [GameEvent(type=GameEventType.HIT, actor="Goblin 1", target="hero")],
        "mage",
    )
    sound_bank.play_events(
        [
            GameEvent(type=GameEventType.HIT, actor="Goblin 1", target="hero"),
            GameEvent(type=GameEventType.DEATH, actor="hero"),
        ],
        "mage",
    )

    assert hit.play_count == 1
    assert burst.play_count == 1
    assert hurt.play_count == 1
    assert death.play_count == 1


def test_act_two_mage_crate_uses_magic_hit_and_break_layers():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    magic_hit = FakeSound()
    chest_break = FakeSound()
    sound_bank = ActTwoSoundBank(
        {"mage_hit": [magic_hit], "chest_break": [chest_break]}
    )
    event = GameEvent(
        type=GameEventType.ATTACK,
        actor="hero",
        data={"kind": "breakable_crate"},
    )

    sound_bank.play_events([event], "mage")

    assert magic_hit.play_count == 1
    assert chest_break.play_count == 1
