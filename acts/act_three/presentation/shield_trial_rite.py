from acts.act_three.presentation.trial_apparitions import draw_rite


def draw_completion(context, trial, now):
    origin = trial["completion_origin"]
    draw_rite(context, "paladin", now - trial["completed"], origin)
