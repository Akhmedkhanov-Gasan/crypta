# Wooden ironbound crate

- `wooden_ironbound.png`: 576x64 RGBA sheet, nine 64x64 tiles in one row. Tile 0 is intact; tiles 1-8 are destruction frames.
- `wooden_ironbound_destruction.png`: 512x64 RGBA sheet, eight destruction frames in order.
- `frames/intact.png`: intact 64x64 sprite.
- `frames/destroy_01.png` through `destroy_08.png`: individual 64x64 destruction frames.
- `source/original.png`: unmodified imagegen output.
- `source/prompt.txt`: generation prompt; references were `level/items.png` and `level/my_tiles_textured_v21.png`.
- `source/preview_2x.png`: enlarged preview on a dark background, not a game asset.

Tiled import: tile width 64, tile height 64, margin 0, spacing 0.
Suggested destruction timing: 50, 50, 60, 60, 70, 80, 90, 120 ms. Play once and retain the final debris frame if needed; Tiled tile animations normally loop.

All frames use a consistent scale and ground baseline around y=54. The source was cropped at a fixed 384x384 size per frame and reduced to 64x64 with bicubic sampling, preserving alpha. Source column centers: 222, 622, 1026; row baselines: 353, 778, 1181. Each crop starts at center x minus 192 and baseline y minus 324.

PNG dimensions and alpha were inspected, and the assembled strip was visually reviewed. No game, build, or project tests were run.
