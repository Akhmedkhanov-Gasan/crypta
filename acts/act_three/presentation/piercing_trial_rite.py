from acts.act_three.presentation.trial_apparitions import draw_rite


def draw_completion(context, trial, now):
    if trial["phase"] != "complete":
        return
    origin = (context.floor.player_column, context.floor.player_row)
    draw_rite(context, "archer", now - trial["completed"], origin)
