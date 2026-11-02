"""Small Cairo drawing helpers shared by characters, props and scenes."""
import math

OUTLINE_HEX = "3b2340"
OUTLINE_W = 6


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


OUTLINE = hexc(OUTLINE_HEX)


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t):
    t = clamp(t)
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def fill_stroke(ctx, fill, width=OUTLINE_W, outline=OUTLINE):
    ctx.set_source_rgba(*fill)
    if width:
        ctx.fill_preserve()
        ctx.set_source_rgba(*outline[:3], outline[3] * fill[3])
        ctx.set_line_width(width)
        ctx.stroke()
    else:
        ctx.fill()


def ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def heart(ctx, cx, cy, s):
    ctx.new_sub_path()
    ctx.move_to(cx, cy + 0.6 * s)
    ctx.curve_to(cx - 1.2 * s, cy - 0.1 * s, cx - 0.6 * s, cy - 1.0 * s, cx, cy - 0.35 * s)
    ctx.curve_to(cx + 0.6 * s, cy - 1.0 * s, cx + 1.2 * s, cy - 0.1 * s, cx, cy + 0.6 * s)
    ctx.close_path()


def cloud(ctx, cx, cy, s):
    """Puffy cloud path centred on (cx, cy), roughly 2.4s wide."""
    for dx, dy, r in ((-0.75, 0.15, 0.45), (-0.25, -0.2, 0.6), (0.35, -0.1, 0.55), (0.85, 0.2, 0.4), (0.0, 0.25, 0.5)):
        ellipse(ctx, cx + dx * s, cy + dy * s, r * s, r * s)


def puff(ctx, cx, cy, s, fill, width=OUTLINE_W):
    """Cloud with a single outline around the whole shape (not every circle)."""
    cloud(ctx, cx, cy, s)
    if width:
        ctx.set_source_rgba(*OUTLINE[:3], OUTLINE[3] * fill[3])
        ctx.set_line_width(width * 2)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*fill)
    ctx.fill()


def text(ctx, s, x, y, size, color, font="Archivo Black", align="center"):
    ctx.select_font_face(font)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    tx = x - ext.width / 2 - ext.x_bearing if align == "center" else x
    ctx.move_to(tx, y - ext.height / 2 - ext.y_bearing)
    ctx.text_path(s)
    fill_stroke(ctx, color, width=5)
