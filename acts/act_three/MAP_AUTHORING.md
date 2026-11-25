# Act Three maps

The current route contains the Oracle arena after awakening and two generated floors. The arena shares `location_id` with the final Act Two floor, so changing presentation does not advance the tower floor number.

## Room templates

Save room templates in `assets/maps/act_3/rooms` or its subdirectories as `room_*.tmx` or `corridor_*.tmx`. The generator discovers nested templates in both loose and packed resources. Keep story rooms in `key_rooms` and configure their paths explicitly. Entry and exit templates are configured separately.

Use finite orthogonal maps with square 64 px tiles and CSV tile layers. Keep the existing rendering layer prefixes. Use the `Ground` layer for floor tiles and `Blocked` or `Collision` for solid collision rectangles. Thin `Barriers` rectangles block movement between cells.

Place point objects in `Connectors`:

- `exit_north`, `exit_south`, `exit_east`, `exit_west`: structural connections on the corresponding outermost cell of the map.
- Add suffixes to distinguish multiple openings on one side, such as `exit_east_upper` and `exit_east_lower`. Each point remains a separate one-cell opening.
- `exit_back`: a return gate, temporarily sealed.
- `exit_up` or `exit_next_floor`: a forward gate. Place it above its walkable approach cell.

Structural connectors currently support one-cell openings. Each connector and its inward neighbor must be walkable and reachable from the other structural connectors. Rooms are placed without rotation. Every structural opening on a generated floor must be joined to another room. Additional corridor pieces can exceed `generated_piece_count`. If a layout cannot fit, the generator can retry with up to two fewer connecting pieces.

The current generated floors set `allow_dead_ends` to `false`. Ordinary one-entrance templates remain available in `room_dead_end` for later use. Free branches are connected back to the floor with authored two-entrance rooms, L-junctions and straight corridors. Required NPC and trial rooms keep their authored entrances. Paired two-entrance terminal rooms remain usable as short loops.

Closely spaced paired openings are joined to matching paired openings in a neighboring template. Matching uses grid positions, opposite directions and opening widths. The generator resolves these connections before placing more rooms, and rejects placements that would cover another opening with a wall. Each generated floor starts from a randomly selected paired-opening room, then adds ordinary connecting rooms, the entry and all required rooms. The selected room is retained in the completed floor. Templates whose openings all face one direction serve as matching terminal rooms. Matching neighbors are added beyond the base piece count. Two separate 7x7 dead ends cannot close openings spaced only two or three cells apart.

The entry template needs a `Spawn` point in `Entities`. Keep its `exit_back` approach clear. The exit template needs one forward gate. Map coordinates and object names determine behavior; object colors and visibility do not affect collision.

## Enemies

Add a boolean map property named `enemy_spawn_mode`:

- `true`: keep authored enemies and allow additional random enemies.
- `false` or absent: keep authored enemies only.

Random enemies require reachable Ground cells, free footprints and clearance from the player and connectors. Manual enemies count toward the floor and room limits. Invalid manual enemy placement reports an error instead of moving or removing the enemy.

Initial targets are 12–16 total enemies on the second Act Three map and 18–24 on the third. Space, room limits and map flags can reduce those counts. The arena uses only its authored enemies. Balance lives in `acts/act_three/settings.py` under `ACT_THREE_ENCOUNTER_SETTINGS`.

Use an enemy type as the point name in `Entities` or `Enemies`, or use `enemy` with an `enemy_type` string property. Hand-authored NPCs, ores, chests and potions are retained.

## Ores

Place point objects named `black_ore` / `black_ores` or `iron_ore` / `iron_ores` in `Ores` or `Entities`. The optional integer property `state` selects stages 1–4. Each interaction advances one stage; the final hit grants one matching ore chunk in a separate inventory slot. Stage 4 is depleted and walkable. Ore definitions and assets are configured in `acts/act_three/mining/catalog.py`.

`bloodvein_ore` / `bloodvein_ores` adds dark turquoise ore with red veins. It uses the same four stages and mining rules. Authored sprites are loaded from `assets/sprites/act_3/items/ores/bloodvein_ore`, using `bloodvein_ore_01.png` through `bloodvein_ore_04.png` and `bloodvein_ore_chunk.png`. Random bloodvein placement is disabled for now; floors 9 and 10 generate iron and black ore only.

Random ore placement follows the same room regions and edge placement as crates. Map properties:

- `ore_spawn_mode` (boolean): allow or disable random veins; defaults to `enemy_spawn_mode` when absent.
- `ore_types` (string): optional comma-separated ore types; random placement uses only types enabled in that floor's `weights`. Currently these are `iron_ore,black_ore`.
- `ore_count` (integer): optional cap on active veins in this room, including authored veins; zero disables extra veins.

Authored veins are retained regardless of the random spawn flag. Random veins avoid occupied cells, decorated tiles, NPC approaches, trial areas and room connectors. Placement preserves walking routes and mining access. Floor targets, ore weights, density and spacing are configured in `acts/act_three/mining/settings.py`; available space can reduce the final count. Iron is prioritized until at least four active iron veins exist on the floor, when room properties and space allow it.

Floors 9 and 10 each target nine iron veins and five black veins, including authored veins: 18 iron and 10 black chunks in total. Weapon and armour ranks I–II together cost 16 iron and eight black chunks. Corridor templates never receive random veins. Each candidate must fit inside a connected open 3x3 patch, remain at least five cells from another vein, and stay outside the two-cell buffer around room entrances. Connectivity checks still apply after placement.

Forge ranks I–III require four iron, then four iron plus four black ore, then four of each of those plus four bloodvein ore. Materials can be worked in across multiple visits; weapon and armour progress are separate, and stat bonuses apply only after a whole rank is finished. Ranks IV–V are reserved and cannot consume materials yet. The blacksmith's keyring is a gift and does not consume the iron shown during the quest.

The forge bar shows only the current rank's material progress. One iron chunk fills 25% of rank I; completing the rank fills the bar during tempering, then resets it for the next rank. A/D selects weapon or armour, Space confirms work, and Escape closes the forge.

## Tilesets and trials

Use external TSX files from `assets/maps/act_3` or its `torches` directory. Each TMX may use its own `firstgid` order; loading remaps it to the shared catalog. After expanding a tileset, update overlapping `firstgid` ranges in Tiled before painting more tiles.

Trials stay under `assets/maps/act_3/trials` and are added as a separate branch on the second map. Their absence of `enemy_spawn_mode` disables random enemies. Existing subclass trial selection remains in place.

Start a new run when checking generation changes. Previously visited floors retain their saved layout and entities.
