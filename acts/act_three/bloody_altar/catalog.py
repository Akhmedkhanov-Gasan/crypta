from dataclasses import dataclass


@dataclass(frozen=True)
class Pact:
    id: str
    name: str
    description: str
    rarity: str = "common"
    precursor: str | None = None
    icon: str | None = None


PACTS = (
    Pact("blood_carapace", "Blood Carapace", "Take 35% less attack damage.\nYou cannot dodge or block.", icon="blood_carapac"),
    Pact("final_word", "Final Word", "+60% damage against foes at half HP or less.\n-30% against healthier foes."),
    Pact("insatiable_edge", "Insatiable Edge", "Consecutive basic attacks: +15% damage, up to +60%. Other actions or misses reset it.\n40% less healing."),
    Pact("exposed_heart", "Exposed Heart", "+0.75 critical damage multiplier.\nEnemy attacks have a 20% chance to deal double damage.", icon="Exposed Heart"),
    Pact("lone_prey", "Lone Prey", "+40% damage against isolated foes.\n-25% against grouped foes. Group radius: 5 cells."),
    Pact("feast_of_many", "Feast of Many", "+40% damage against grouped foes.\n-25% against isolated foes. Group radius: 5 cells."),
    Pact("deaths_reprieve", "Death's Reprieve", "Lethal hit: 1 HP, refill skills, stun nearby foes. Recharge: 15 original kills.\n-30% max HP; -50% healing while spent.", "legendary", icon="death’s_reprieve"),
    Pact("black_tribute", "Black Tribute", "+100% damage.\nTraders, smiths and rune masters permanently refuse all services.", "legendary"),
    Pact("crimson_rupture", "Crimson Rupture", "Every direct hero hit causes bleeding: 20% damage for 3 turns.\n60% less healing.", "rare", "open_wound"),
    Pact("shattered_seal", "Shattered Seal", "E charges in one hit.\nEach cast costs 5% max HP and can kill. The lost E rune cannot return.", "rare", "broken_seal"),
    Pact("splintered_heart", "Splintered Heart", "+75% damage.\nLose 40% maximum HP, replacing Glass Heart's original sacrifice.", "rare", "glass_heart"),
    Pact("endless_hunger", "Endless Hunger", "Heal for 40% of direct hero damage.\nTake 50% more attack damage. All other healing is forbidden.", "rare", "blood_hunger"),
)
PACTS_BY_ID = {pact.id: pact for pact in PACTS}
RARITY_WEIGHTS = {"common": 100, "rare": 35, "legendary": 6}
RARITY_COLORS = {"common": (167, 167, 167), "rare": (184, 126, 192), "legendary": (211, 160, 75)}


def has_pact(player, identifier):
    return player.act_three.altar_pact_id == identifier


def services_are_blocked(player):
    return has_pact(player, "black_tribute")


def eligible_pacts(player):
    if player.act_three.altar_pact_id is not None:
        return ()
    return tuple(pact for pact in PACTS
                 if pact.precursor is None or player.act_two.bloody_pact_id == pact.precursor)
