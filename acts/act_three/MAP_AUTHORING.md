# Act Three maps

The current route contains the Oracle arena after awakening and two generated floors. The arena shares `location_id` with the final Act Two floor, so changing presentation does not advance the tower floor number.

## Room templates

Save ordinary templates in `assets/maps/act_3/rooms` as `room_*.tmx` or `corridor_*.tmx`. Entry and exit templates are configured separately. The generator uses every ordinary template at least once before repeating templates.

Use finite orthogonal maps with square 64 px tiles and CSV tile layers. Keep the existing rendering layer prefixes. Use the `Ground` layer for floor tiles and `Blocked` or `Collision` for solid collision rectangles. Thin `Barriers` rectangles block movement between cells.

Place point objects in `Connectors`:

- `exit_north`, `exit_south`, `exit_east`, `exit_west`: structural connections on the corresponding outermost cell of the map.
- `exit_back`: a return gate, temporarily sealed.
- `exit_up` or `exit_next_floor`: a forward gate. Place it above its walkable approach cell.

Structural connectors currently support one-cell openings. Each connector and its inward neighbor must be walkable and reachable from the other structural connectors. Unused openings are sealed by the generator. Rooms are placed without rotation.

The entry template needs a `Spawn` point in `Entities`. Keep its `exit_back` approach clear. The exit template needs one forward gate. Map coordinates and object names determine behavior; object colors and visibility do not affect collision.

## Enemies

Add a boolean map property named `enemy_spawn_mode`:

- `true`: keep authored enemies and allow additional random enemies.
- `false` or absent: keep authored enemies only.

Random enemies require reachable Ground cells, free footprints and clearance from the player and connectors. Manual enemies count toward the floor and room limits. Invalid manual enemy placement reports an error instead of moving or removing the enemy.

Initial targets are 12–16 total enemies on the second Act Three map and 18–24 on the third. Space, room limits and map flags can reduce those counts. The arena uses only its authored enemies. Balance lives in `acts/act_three/settings.py` under `ACT_THREE_ENCOUNTER_SETTINGS`.

Use an enemy type as the point name in `Entities` or `Enemies`, or use `enemy` with an `enemy_type` string property. Hand-authored NPCs, ores, chests and potions are retained.

## Tilesets and trials

Use external TSX files from `assets/maps/act_3` or its `torches` directory. Each TMX may use its own `firstgid` order; loading remaps it to the shared catalog. After expanding a tileset, update overlapping `firstgid` ranges in Tiled before painting more tiles.

Trials stay under `assets/maps/act_3/trials` and are added as a separate branch on the second map. Their absence of `enemy_spawn_mode` disables random enemies. Existing subclass trial selection remains in place.

Start a new run when checking generation changes. Previously visited floors retain their saved layout and entities.
