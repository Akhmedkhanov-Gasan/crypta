# Act III balance contract

This is the implementation baseline for a difficult Act III, including the
planned blood-pact system. Numerical settings require playtesting; static
analysis does not establish clear rates or prove equal subclass strength.
The new altar UI and twelve new pacts are not integrated by this change.

## Progression

Act I and Act II keep their existing attribute rank limit of 10, combat-stat
limits, XP curve, one attribute point per level, and attribute health gains.
An awakened Act III character uses the following rules, including when
revisiting earlier floors:

- Attribute ranks have no limit. Each level earned after awakening grants
  two attribute points. The existing XP curve and enemy XP rewards stay intact.
- Valor keeps its alternating physical damage growth, +0.05 critical damage
  per rank, and +1 maximum HP every two ranks.
- Will keeps magical attack scaling and +0.03 critical damage per rank.
- Fortitude grants +2 maximum HP per rank. Increasing maximum HP through
  attribute investment does not restore current HP in Act III.
- Critical damage is no longer limited to x2.75.
- Critical chance gains are linear up to 45%, then diminish toward 75%.
- Dodge gains are linear up to 35%, then diminish toward 60%.
- The diminishing curve has no rank cutoff: additional investment continues
  to improve probability without providing guaranteed avoidance.
- Starting from the diminishing thresholds, ten extra Instinct ranks raise
  critical chance to approximately 67.1% and dodge to approximately 52.5%.
- Attribute previews must not mutate real ranks, current health, or pact costs.

E continues to require four successful hits, or two with Broken Seal.
Passive E runes do not charge. Every successful qualifying hit grants one
charge to Q and F. There is no mastery progression or charge-rate multiplier.
Q remains a reward for the subclass trial. F is reserved for defeating the
designated boss on tower floor 11, not for earning character levels.
Newly unlocked abilities receive one full charge in their actual
subclass counter; repeated unlock requests do not refill them.
At level rewards, the log reports the actual number of attribute points gained.

Floor 11 and its boss are not yet authored. When adding that floor, set its
`ultimate_unlock_boss` configuration field to the boss enemy type. The defeat
handler requires this exact type, tower floor 11, Act III presentation, a dead
non-summoned enemy, and a player who has not already unlocked F. Ordinary
enemies, other bosses, other floors, levels, and repeated rewards do not unlock
or refill F. The existing unlocked-slot set persists the reward.

The HUD does not show mastery tracks or a charge-rate row. Old HUD JSON may
still contain these fields; the loader ignores them. New Figma HUD exports
do not require or emit them. Existing already-unlocked abilities in saves
are retained; the change does not revoke earlier progression.

## Combat and equipment

Act III's generic attack resolver combines critical damage, curse, rage,
weapon rank, inherited Glass Heart, and ability multipliers before rounding.
Tower Shield retains its fractional-damage accumulator. Act II's attack
calculation retains its previous behavior.

Weapon tempering grants +10% damage per rank. The same bonus applies to
hero attacks, phantoms, familiars/totems, and Greater Manifestation routed
through the generic resolver. Glass Heart also affects those owned attacks.
Possessed creatures retain their own creature attack rules and stats.

Armor tempering grants 7% physical damage reduction per rank: 7%, 14%, 21%,
28%, 35%. Only the first three forge ranks currently have implemented
materials. Armor does not reduce magical attacks, HP costs, or every hazard.
Its reduction multiplies with other reductions rather than adding to them.

## Subclass roles and pressure points

| Subclass | Core investment and role | Balance constraints |
| --- | --- | --- |
| Assassin | Valor for direct damage, Instinct for critical hits, ambush and reactive counters, Fortitude for survival | Dodge has diminishing returns. Q uses its real three-charge requirement. Ultimate strikes do not refill the ultimate. High critical damage remains a deliberate burst investment. |
| Archer | Valor for ranged damage, Instinct for critical hits, positioning and line attacks | Flat shot bonus is +1 instead of +2. Range remains three cells while enemy archers reach six. Extra arrows and phantom attacks do not generate free ability charge. |
| Berserker | Valor and Fortitude; damage rises at low health, temporary survival window | Rage multipliers remain x1.25/x1.5. Last Rage cannot refill while its protection is active. Death Wish cannot extend protection by farming summoned enemies. Healing restrictions remain meaningful. |
| Paladin | Valor/Fortitude for the frontline, optional Will investment for Sacred Ground | Tower Shield grants +25 percentage points of block, caps total block at 65%, and reduces outgoing damage by 25%. Fervent Crusade still disables block and dodge. Armor and avoidance cannot simply add up to immunity. |
| Warlock | Will for projectiles and area damage; Curse and Demon Form amplify committed attacks | Curse lasts six turns instead of ten, with its x1.5 damage multiplier unchanged. Summoned enemies provide no Demon Form kill healing. Blood Pact still charges HP costs and requires careful sustain. |
| Summoner | Will for hero and spirit damage, Fortitude for player and spirit durability | Familiars inherit weapon scaling. Hero damage remains 65% while the familiar is away. Greater Manifestation requires eight charges. Host transfers cost charged Q. Captured healers only heal during nearby visible combat. Soul Devourer cannot farm summoned enemies for souls or healing. |

Active berserker, paladin, and summoner ultimates do not accumulate their next
activation through successful-hit charging while active. Archer phantoms have
finite ammunition; their own attacks do not refill F. Warlock forms retain
their existing transformation and reversion rules. Receiving damage still
contributes to the existing berserker/summoner ultimate mechanics.

## Enemy baseline

These values apply on the first full combat floor, act_floor 2:

| Enemy | HP | Main attack | Additional pressure |
| --- | ---: | --- | --- |
| Goblin | 16 | 4-5 | Group frontline and existing reinforcement behavior |
| Brute | 30 | 7-9 | Telegraphs cleave; punishes committing to a bad tile |
| Archer | 14 | 4-5 ranged, 3 melee | Range six; forces ranged builds to reposition |
| Sentinel | 32 | 6-8 | Existing guard and counter mechanics remain |
| Priest | 18 | 4-6 magic, 3 melee | Heals four HP; priority target behind the frontline |
| Priest ghost | 14 | 5-7 magic, 3-4 melee | Dodge reduced from 60% to 35% to reduce miss streaks |
| Lantern Warden | 260 | 7-8 melee; abilities 7-14 | Existing telegraphs, patterns, and recovery opportunities remain |

At act_floor 3, regular enemies gain x1.25 HP, rounded upward, +1 damage
for every attack mode, and +1 healing where applicable. For example, a brute
has 38 HP and deals 8-10 damage. Additional authored future depths repeat
the x1.25 HP increase and add one more damage/healing per depth.
Lantern Warden is excluded from this automatic regular-enemy depth curve.
There is no scaling based on the player's attributes, equipment or selected
pact: investing in a build must produce a real advantage.

Population targets remain 24-30 and 32-38 enemies, with existing spatial
constraints, maximums of five/six enemies per room, one priest per room,
and at most two archers. Stronger individual enemies do not also require a
large population increase. Unsafe entrance spawns remain disallowed.

Subclass tutorial trials retain their authored stats. The Rune Master's
four combat waves use the Act III floor-three baseline, with HP multipliers
of 1.00, 1.08, 1.16 and 1.24 across the waves. Existing openings and
intermissions remain. The trial does not use the weak Act I baseline.

## Pact integration requirements

The approved catalogue remains unchanged: Blood Carapace, Final Word,
Insatiable Edge, Exposed Heart, Lone Prey, Feast of Many, Death's Reprieve,
Black Tribute, Crimson Rupture, Shattered Seal, Splintered Heart, Endless Hunger.
The last four require their Act II precursor and replace it rather than
stacking with it. Shattered Seal uses a 5% maximum-HP activation cost.

For the current two combat floors, start with one guaranteed optional altar
on the first combat floor, offering three distinct weighted choices and
allowing one accepted new pact or evolution in the act. This remains a
design starting point, not a newly implemented acquisition system.
Evaluate a second selection only after observing the first set of builds.
Balance the mandatory route for a character who declines every pact.

Specific interactions to preserve when implementing the new pacts:

- Apply contextual pact damage to the same final multiplier stage, then round
  once. Evaluate Final Word against health before the hit, not after it.
- Blood Carapace disables both defensive rolls. Its 35% reduction multiplies
  with armor, and must not be added to armor percentages.
- Lone Prey and Feast of Many are mutually exclusive. Evaluate other hostile
  creatures within five cells of the target, excluding the target and allies.
- Exposed Heart's +0.75 critical multiplier is not lost to the old x2.75 cap.
  Its enemy critical multiplier must apply before defensive reductions.
- Insatiable Edge tracks ordinary player attacks, not companions, counterattacks,
  extra arrows, or bleed ticks. Non-turn-consuming UI actions do not reset it.
- Shattered Seal's 5% HP cost rounds upward, bypasses defense and can kill.
  Charge gains must not bypass its HP cost or the lost E rune.
- Health-sacrifice pacts must retain their percentage cost after future
  maximum-HP gains. Existing Glass Heart already does so in Act III.
- Endless Hunger's 40% life steal uses actual health lost, excluding overkill,
  companions and bleed. Its +50% incoming attack damage remains mandatory;
  all other healing must be rejected through the shared healing rules.
- Summoned enemies must not restore Death's Reprieve or provide inexhaustible
  kill healing, souls, protection extensions, XP or loot.
- Death's Reprieve starts charged and needs 15 distinct original-enemy kills
  after use. Changing floors, reloading or waiting must not restore it.
- Black Tribute provides +100% damage and permanently disables NPC services
  except the teleport NPC. Already owned equipment and supplies remain usable.
  Preparing before acceptance is an intentional advantage, not an exploit to
  remove. Its rarity and irreversible lost services are part of its price.
- Save offers, accepted pacts, cooldown/kill progress and permanent sacrifices.
  Reopening the altar or moving between floors must not reroll anything.

## Validation and playtest targets

`tools/check_act_three_balance.py` covers rank isolation, diminishing returns,
critical-damage growth, preview isolation, health-sacrifice persistence,
level rewards and boss-gated F, subclass charge counters, magical scaling above
rank ten, final damage rounding, companion inheritance, and depth scaling.
The focused existing rune checks cover their specific mechanics and should
also be run after authorization.

Manual playtests should cover all six subclasses with no pact, the inherited
Act II pact, an ordinary new pact, and a legendary/evolution offer. Include
physical and magical incoming attacks, missed/blocked hits, boss telegraphs,
low-HP investment, waiting outside combat, returning to earlier floors,
and saving/loading after every progression milestone.

Review death causes and turns-to-kill, not just average damage. A declined
pact must remain viable; a good pact should create a strong build with an
observable failure condition. Enemy critical-hit pacts can intentionally
create lethal risk, but the mandatory baseline must retain readable attacks
and opportunities to disengage.
