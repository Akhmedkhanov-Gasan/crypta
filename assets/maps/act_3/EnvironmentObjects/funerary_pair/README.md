# Funerary urn pair

Two asymmetrically arranged funerary vessels form one breakable object.

- `funerary_pair.png`: 576x64 RGBA sheet. Tile 0 is intact; tiles 1-8 are successive destruction frames.
- `funerary_pair_destruction.png`: 512x64 RGBA sheet containing only the eight destruction frames.
- `frames/intact.png`: intact 64x64 sprite.
- `frames/destroy_01.png` through `destroy_08.png`: individual 64x64 destruction frames.
- `source/original.png`: unmodified built-in imagegen output.
- `source/prompt.txt`: full generation prompt. Style reference: `level/items.png`; layout reference: `level/crates/wooden_ironbound/source/original.png`.
- `source/preview_2x.png`: enlarged preview on a dark background, not a game asset.

Tiled import: tile width 64, tile height 64, margin 0, spacing 0.
Suggested destruction timing: 50, 50, 60, 60, 70, 80, 90, 120 ms. Play once and optionally retain the final debris frame. Tiled tile animations normally loop.

The source is 1254x1254 with nine 418x418 cells. Each cell was isolated before resampling to avoid neighboring-frame contamination. Fixed 448x448 sampling windows were reduced to 64x64 using bicubic sampling. Source column centers: 222, 622, 1030; row baselines: 351, 775, 1189. Sampling windows start at center x minus 224 and baseline y minus 378. Output ground baseline is y=54. Alpha below 4 was cleared to remove near-invisible residue.

PNG dimensions, alpha format and side-edge padding were checked; the assembled preview was visually inspected. No game, build or project tests were run.
