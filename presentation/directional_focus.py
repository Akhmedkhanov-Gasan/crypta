def move_focus(rectangles, focus, direction):
    origin = rectangles[focus].center
    dx, dy = direction
    candidates = []
    for name, rectangle in rectangles.items():
        x = rectangle.centerx - origin[0]
        y = rectangle.centery - origin[1]
        forward = x * dx + y * dy
        if forward <= 0:
            continue
        sideways = abs(x * dy - y * dx)
        candidates.append((forward + 3 * sideways, sideways, name))
    return min(candidates)[2] if candidates else focus
