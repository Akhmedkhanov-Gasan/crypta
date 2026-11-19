from acts.act_three.presentation.trial_apparitions import draw_rite


def draw_completion(context, trial, elapsed):
    draw_rite(context, "assassin", elapsed, trial["final"])
