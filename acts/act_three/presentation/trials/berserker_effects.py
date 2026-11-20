from acts.act_three.presentation.trials.apparitions import draw_rite


def draw_completion(context, trial, now):
    origin = trial["completion_origin"]
    draw_rite(context, "berserker", now - trial["completed"], origin)
