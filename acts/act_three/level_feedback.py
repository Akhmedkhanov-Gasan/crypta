def start_level_up_effect(player, started_at, amount=1):
    player.act_three.level_up_effect_started_at = started_at
    player.act_three.level_up_effect_amount = max(1, amount)
