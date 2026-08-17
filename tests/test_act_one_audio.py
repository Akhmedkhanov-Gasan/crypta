import pytest

import presentation.audio as audio_module
from acts.act_two.state import FireZoneState
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


def test_act_two_player_potion_heal_plays_common_sound():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    healing = FakeSound()
    sound_bank = ActTwoSoundBank({"player_heal": [healing]})
    event = GameEvent(
        type=GameEventType.HEAL,
        actor="hero",
        target="hero",
        data={"kind": "potion"},
    )

    sound_bank.play_events([event], "rogue")

    assert healing.play_count == 1


def test_act_two_enemy_sounds_fade_with_distance_and_stop_after_eight_cells():
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

    class FakeFloor:
        player_column = 0
        player_row = 0
        enemies = ()

    attack = FakeSound()
    sound_bank = ActTwoSoundBank({"goblin_attack": [attack]})
    near_attack = GameEvent(
        type=GameEventType.ATTACK,
        actor="Goblin 1",
        origin=(3, 0),
        data={"enemy_type": "goblin"},
    )
    far_attack = GameEvent(
        type=GameEventType.ATTACK,
        actor="Goblin 2",
        origin=(9, 0),
        data={"enemy_type": "goblin"},
    )

    sound_bank.play_events([near_attack], "warrior", FakeFloor())
    sound_bank.play_events([far_attack], "warrior", FakeFloor())

    assert len(attack.channels) == 1
    assert attack.channels[0].volume == pytest.approx(0.68 * 0.74)


def test_act_two_enemy_death_replaces_hurt_and_sentinel_block_is_distinct():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    goblin_hurt = FakeSound()
    goblin_death = FakeSound()
    sentinel_block = FakeSound()
    sound_bank = ActTwoSoundBank(
        {
            "goblin_hurt": [goblin_hurt],
            "goblin_death": [goblin_death],
            "sentinel_block": [sentinel_block],
        }
    )
    events = [
        GameEvent(
            type=GameEventType.HIT,
            actor="hero",
            target="Goblin 1",
            destination=(1, 0),
            data={"enemy_type": "goblin", "blocked": False},
        ),
        GameEvent(
            type=GameEventType.DEATH,
            actor="Goblin 1",
            destination=(1, 0),
            data={"enemy_type": "goblin"},
        ),
        GameEvent(
            type=GameEventType.HIT,
            actor="hero",
            target="Sentinel 1",
            destination=(1, 1),
            data={"enemy_type": "sentinel", "blocked": True},
        ),
    ]

    sound_bank.play_events(events, "mage")

    assert goblin_hurt.play_count == 0
    assert goblin_death.play_count == 1
    assert sentinel_block.play_count == 1


def test_act_two_player_death_suppresses_every_other_sound_in_the_turn():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    death = FakeSound()
    footstep = FakeSound()
    enemy_attack = FakeSound()
    hurt = FakeSound()
    sound_bank = ActTwoSoundBank(
        {
            "warrior_death": [death],
            "warrior_hurt": [hurt],
            "footstep": [footstep],
            "brute_attack": [enemy_attack],
        }
    )
    events = [
        GameEvent(type=GameEventType.MOVE, actor="hero"),
        GameEvent(
            type=GameEventType.ATTACK,
            actor="Brute 1",
            data={"enemy_type": "brute"},
        ),
        GameEvent(type=GameEventType.HIT, actor="Brute 1", target="hero"),
        GameEvent(type=GameEventType.DEATH, actor="hero"),
    ]

    sound_bank.play_events(events, "warrior")

    assert death.play_count == 1
    assert hurt.play_count == 0
    assert footstep.play_count == 0
    assert enemy_attack.play_count == 0


def test_act_two_fire_tick_plays_enemy_hurt_sound():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    goblin_hurt = FakeSound()
    sound_bank = ActTwoSoundBank({"goblin_hurt": [goblin_hurt]})
    game_state = create_game_state(3)
    goblin = next(
        enemy for enemy in game_state.floor.enemies
        if enemy.type == "goblin"
    )
    goblin.column = game_state.floor.player_column + 1
    goblin.row = game_state.floor.player_row

    sound_bank.play_events(
        [
            GameEvent(
                type=GameEventType.HIT,
                actor="fire",
                target=goblin.name,
                destination=(goblin.column, goblin.row),
                amount=1,
                data={"kind": "fire_bomb", "enemy_type": "goblin"},
            )
        ],
        "rogue",
        game_state.floor,
    )

    assert goblin_hurt.play_count == 1


def test_act_two_fire_bomb_audio_loops_until_zone_ends(monkeypatch):
    class FakeChannel:
        def __init__(self):
            self.play_calls = []
            self.fadeouts = []
            self.volume = None

        def play(self, sound, loops=0, fade_ms=0):
            self.play_calls.append((sound, loops, fade_ms))

        def fadeout(self, duration):
            self.fadeouts.append(duration)

        def set_volume(self, volume):
            self.volume = volume

    class FakeMixer:
        def __init__(self):
            self.channels = {
                index: FakeChannel() for index in range(8)
            }

        @staticmethod
        def get_init():
            return 44100, -16, 2

        @staticmethod
        def get_num_channels():
            return 8

        @staticmethod
        def set_num_channels(_count):
            return None

        def Channel(self, index):
            return self.channels[index]

    fake_mixer = FakeMixer()
    monkeypatch.setattr(audio_module.pygame, "mixer", fake_mixer)
    sounds = {
        "fire_bomb_break": [object()],
        "fire_bomb_ignite": [object()],
        "fire_bomb_burning": [object()],
    }
    sound_bank = ActTwoSoundBank(sounds)
    game_state = create_game_state(3)
    game_state.floor.fire_zones = [
        FireZoneState(
            center=(
                game_state.floor.player_column + 1,
                game_state.floor.player_row,
            ),
            cells=(),
            origin=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            created_at=100,
            ticks_remaining=8,
        )
    ]

    sound_bank.update_fire_bomb_audio(game_state.floor, 519)
    assert fake_mixer.channels[5].play_calls == []

    sound_bank.update_fire_bomb_audio(game_state.floor, 520)
    assert len(fake_mixer.channels[5].play_calls) == 1

    sound_bank.update_fire_bomb_audio(game_state.floor, 610)
    assert len(fake_mixer.channels[6].play_calls) == 1

    sound_bank.update_fire_bomb_audio(game_state.floor, 740)
    loop_calls = fake_mixer.channels[7].play_calls
    assert len(loop_calls) == 1
    assert loop_calls[0][1:] == (-1, 180)

    sound_bank.update_fire_bomb_audio(game_state.floor, 20000)
    assert len(fake_mixer.channels[7].play_calls) == 1

    game_state.floor.fire_zones = []
    sound_bank.update_fire_bomb_audio(game_state.floor, 20001)
    assert fake_mixer.channels[7].fadeouts[-1] == 280
    assert sound_bank._fire_bomb_loop_active is False


def test_act_two_room_sounds_and_secret_wall_layers_are_connected():
    class FakeChannel:
        def set_volume(self, volume):
            self.volume = volume

    class FakeSound:
        def __init__(self):
            self.play_count = 0

        def play(self):
            self.play_count += 1
            return FakeChannel()

    sound_keys = (
        "treasury_trap_activate",
        "portcullis_lock",
        "portcullis_unlock",
        "room_reward",
        "secret_wall_break",
        "rogue_hit",
    )
    sounds = {sound_key: FakeSound() for sound_key in sound_keys}
    sound_bank = ActTwoSoundBank(
        {sound_key: [sound] for sound_key, sound in sounds.items()}
    )
    events = [
        GameEvent(
            type=GameEventType.ENVIRONMENT,
            actor="treasury",
            origin=(1, 1),
            data={"kind": sound_key},
        )
        for sound_key in sound_keys[:4]
    ]
    events.append(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            positions=((1, 1),),
            data={"kind": "secret_wall"},
        )
    )

    sound_bank.play_events(events, "rogue")

    assert all(sound.play_count == 1 for sound in sounds.values())
