from acts.act_three.enemies.lantern_warden.behavior import (
    take_lantern_warden_turn,
)
from acts.act_three.enemies.catalog import LANTERN_WARDEN_TYPE


ACT_THREE_ENEMY_TURN_HANDLERS = {
    LANTERN_WARDEN_TYPE: take_lantern_warden_turn,
}
