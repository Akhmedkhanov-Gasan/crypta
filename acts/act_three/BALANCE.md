# Act III balance contract

This is the implementation baseline for a difficult Act III, including the
implemented blood-pact system. Numerical settings require playtesting; static
analysis does not establish clear rates or prove equal subclass strength.
The Figma altar UI, animated world object and twelve new pacts are integrated.

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

E continues to require four successful hits, two with Broken Seal, or one
with its Shattered Seal evolution.
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

Starting at act_floor 3, regular enemy HP grows by 12% of its floor-nine
baseline per additional floor, rounded upward. Damage and healing increase
by one at tower floors 10, 13, 16 and so on. The health curve is linear to
support a long act without exponential damage sponges.

| Tower floor | Brute HP | Brute damage |
| --- | ---: | --- |
| 9 | 30 | 7-9 |
| 10 | 34 | 8-10 |
| 11, future | 38 | 8-10 |
| 12, future | 41 | 8-10 |
| 13, future | 45 | 9-11 |

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

## Bloody altar

The approved catalogue remains unchanged: Blood Carapace, Final Word,
Insatiable Edge, Exposed Heart, Lone Prey, Feast of Many, Death's Reprieve,
Black Tribute, Crimson Rupture, Shattered Seal, Splintered Heart, Endless Hunger.
The last four require their Act II precursor and replace it rather than
stacking with it. Shattered Seal uses a 5% maximum-HP activation cost.

Tower floor 10 contains one guaranteed optional altar in a random reachable
room position. It offers three distinct weighted choices and allows one
accepted new pact or evolution in the act. Offers persist across reopening,
floor changes and saves. Selection and confirmation follow the Rune Master's
interaction: floating cards, eased illumination, animated button presses,
mist on reveal, movement to the center, confirmation light and final fade.
The pact is applied once after the confirmation light, before the final fade.
Left/right or A/D move keyboard focus; 1/2/3 select a card. Space selects
the focused card, then confirms it on a second press. Enter confirms the
selection, or selects the focused card if none is selected. Mouse actions
require pressing and releasing over the same moving control. Backspace or
the return button closes the menu; Escape closes it immediately. Input during
opening and confirmation animations cannot change the selection. The renderer
uses the Rune Master's motion, subpixel sampling, lighting and button effects
with crimson mist, and draws at the window's native resolution.
The object occupies one tile and uses a fixed 64 x 64 base with a separate
64-frame blood/glow/mote overlay. The 3.2-second loop blends adjacent effect
frames; stone geometry never changes. After use, the base dims and effects stop.
New generation is required for floors already stored without an altar.
The `altar` developer command opens this UI anywhere in Act III without
creating or moving a world fixture. In Act II it retains the original altar.
The `baltar` developer command teleports to a free adjacent cell beside the
physical altar on floor 10, reusing the visited floor without changing offers.
Additional procedural blood ripples, seal glow, rising mist, motes and a ground
halo make the active altar visible at native sprite size. These effects stop
after a pact is accepted and never move the stone base.
Internal Act III floor gates work in both directions independently of the
trader quest, including the awakening room. The Act II boundary and the
unimplemented next floor remain sealed. Saved gate destinations are refreshed
when used, and revisits preserve the existing room state.

Common, rare and legendary choices have relative weights 100, 35 and 6.
Each draw contains at most one legendary. Evolutions enter the pool only
when the corresponding Act II pact is currently equipped. Ordinary pacts
retain the inherited Act II pact; evolutions replace their parent.
Evaluate a second selection only after observing the first set of builds.
Balance the mandatory route for a character who declines every pact.

Implemented pact effects and interactions:

- Apply contextual pact damage to the same final multiplier stage, then round
  once. Evaluate Final Word against health before the hit, not after it.
- Blood Carapace disables both defensive rolls. Its 35% reduction multiplies
  with armor, and must not be added to armor percentages.
- Lone Prey and Feast of Many are mutually exclusive. Evaluate other hostile
  creatures within five cells of the target, excluding the target and allies.
  Distance uses the maximum axis separation, including diagonal neighbors.
  Lone Prey grants +40% against isolated targets and -25% against groups;
  Feast of Many reverses these conditions.
- Exposed Heart's +0.75 critical multiplier is not lost to the old x2.75 cap.
  Its enemy critical multiplier must apply before defensive reductions.
  Direct enemy attacks have a 20% chance to deal double damage.
- Insatiable Edge tracks ordinary player attacks, not companions, counterattacks,
  extra arrows, or bleed ticks. Non-turn-consuming UI actions do not reset it.
  Each consecutive basic attack grants +15%, capped at +60%; misses and
  other turn actions reset the chain. Received healing is reduced by 40%.
- Final Word grants +60% against targets at half HP or below and -30%
  against healthier targets. Crimson Rupture adds three turns of bleeding
  at 20% of actual direct hero damage per turn and reduces healing by 60%.
- Shattered Seal's 5% HP cost rounds upward, bypasses defense and can kill.
  Charge gains must not bypass its HP cost or the lost E rune.
- Health-sacrifice pacts must retain their percentage cost after future
  maximum-HP gains. Existing Glass Heart already does so in Act III.
  Splintered Heart grants +75% damage and replaces Glass Heart's 25% maximum
  HP sacrifice with 40%, without healing the player during replacement.
- Endless Hunger's 40% life steal uses actual health lost, excluding overkill,
  companions and bleed. Its +50% incoming attack damage remains mandatory;
  all other healing must be rejected through the shared healing rules.
- Summoned enemies must not restore Death's Reprieve or provide inexhaustible
  kill healing, souls, protection extensions, XP or loot.
- Death's Reprieve starts charged and needs 15 distinct original-enemy kills
  after use. Changing floors, reloading or waiting must not restore it.
  It sacrifices 30% maximum HP, leaves the player at 1 HP on lethal damage,
  charges accessible active abilities and stuns adjacent foes for one turn.
  Healing is reduced by 50% until recharge. Trial waves, revived ghosts and
  creatures emerging from crates cannot recharge it.
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
`tools/check_act_three_altar.py` covers all twelve pact effects, eligibility,
rarity and persistent offers, actual E casts for all three base classes,
NPC service refusal, save roundtrips, mouse/keyboard confirmation, UI and
animation assets, floor-ten reachability and floor-nine generation for all
six subclasses. Rendering checks use an offscreen SDL display.

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
