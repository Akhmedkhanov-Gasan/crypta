from acts.act_one.enemies.catalog import ACT_ONE_ENEMY_TYPES
from acts.act_three.enemies.catalog import ACT_THREE_ENEMY_TYPES
from acts.act_two.enemies.catalog import ACT_TWO_ENEMY_TYPES
from game.enemy_catalog import SHARED_ENEMY_TYPES


ENEMY_TYPES = {
    **SHARED_ENEMY_TYPES,
    **ACT_ONE_ENEMY_TYPES,
    **ACT_TWO_ENEMY_TYPES,
    **ACT_THREE_ENEMY_TYPES,
}
