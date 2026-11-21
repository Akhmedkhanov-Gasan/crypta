_PIXEL_FIELDS = frozenset({
    "x", "y", "width", "height", "size", "corner_radius",
    "stroke_weight", "blur_radius",
})


def scale_figma_layout(value, scale):
    if isinstance(value, list):
        return [scale_figma_layout(item, scale) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if (
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and (
                key in _PIXEL_FIELDS
                or (key == "value" and value.get("unit") == "PIXELS")
            )
        ):
            result[key] = round(item * scale)
        else:
            result[key] = scale_figma_layout(item, scale)
    return result
