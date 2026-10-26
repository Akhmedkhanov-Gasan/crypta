import resource_store as resources

from presentation.layout import FONT_ROOT


def load_act_one_fonts():
    regular_path = FONT_ROOT / "AtkinsonHyperlegible-Regular.ttf"
    bold_path = FONT_ROOT / "AtkinsonHyperlegible-Bold.ttf"
    pixel_path = FONT_ROOT / "PixelOperator.ttf"
    pixel_bold_path = FONT_ROOT / "PixelOperator-Bold.ttf"

    return {
        "title": resources.load_font(str(bold_path), 42),
        "heading": resources.load_font(str(bold_path), 27),
        "status": resources.load_font(str(bold_path), 21),
        "text": resources.load_font(str(regular_path), 19),
        "controls": resources.load_font(str(bold_path), 17),
        "interface": resources.load_font(str(regular_path), 19),
        "hud": resources.load_font(str(pixel_bold_path), 19),
        "hud_small": resources.load_font(str(pixel_path), 16),
    }


def load_act_one_gameplay_assets():
    return {}
