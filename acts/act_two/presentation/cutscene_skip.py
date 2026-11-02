from presentation.cutscene_skip import draw_skip_hint


def draw_cutscene_skip(screen, controller, current_time, font):
    if not controller.is_visible(current_time):
        return

    draw_skip_hint(screen, controller.progress, font)
