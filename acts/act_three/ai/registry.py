from acts.act_three.ai.pursuit import take_pursuit_turn
from acts.act_three.enemies import LANTERN_WARDEN_TYPE


ACT_THREE_ENEMY_TURN_HANDLERS = {
    LANTERN_WARDEN_TYPE: take_pursuit_turn,
}
