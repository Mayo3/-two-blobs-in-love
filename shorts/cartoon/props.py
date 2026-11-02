"""Little animated props the couple interacts with. `lt` is time since the beat started."""
import math

from .draw import OUTLINE, clamp, ease_out_back, ellipse, fill_stroke, heart, hexc, puff, rrect, text

PINK = hexc("ff5d8f")
WHITE = (1, 1, 1, 1)


def hearts_rising(ctx, lt, x, y, n=6, spacing=0.4, size=26):
    for k in range(n):
        age = lt - k * spacing
        if age < 0 or age > 2.2:
            continue
        a = clamp(1 - age / 2.2)
        hx = x + math.sin(age * 3 + k * 1.7) * 34 + (k % 3 - 1) * 30
        hy = y - age * 170
        s = size * (0.7 + 0.3 * ease_out_back(min(1, age * 3)))
        heart(ctx, hx, hy, s)
        fill_stroke(ctx, (*PINK[:3], a), width=5)


def heart_pop(ctx, lt, x, y, size=55):
    if lt < 0:
        return
    s = size * ease_out_back(min(1, lt * 2.5)) * (1 + 0.06 * math.sin(lt * 8))
    heart(ctx, x, y, s)
    fill_stroke(ctx, PINK, width=6)
    ctx.set_source_rgba(1, 1, 1, 0.6)
    ellipse(ctx, x - s * 0.45, y - s * 0.4, s * 0.15, s * 0.1)
    ctx.fill()


def bird(ctx, x, y, t, s=1.0, color="ffd166"):
    flap = math.sin(t * 16)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    # wing behind
    ctx.save()
    ctx.rotate(-0.6 * flap)
    ellipse(ctx, 6, -10, 26, 12)
    fill_stroke(ctx, hexc("f4a940"), width=5)
    ctx.restore()
    ellipse(ctx, 0, 0, 36, 28)
    fill_stroke(ctx, hexc(color), width=5)
    ctx.move_to(-34, -4)
    ctx.line_to(-52, 2)
    ctx.line_to(-33, 8)
    ctx.close_path()
    fill_stroke(ctx, hexc("ff8c42"), width=4)
    ellipse(ctx, -16, -8, 5, 6)
    ctx.set_source_rgba(*OUTLINE)
    ctx.fill()
    ctx.restore()


def phone(ctx, x, y, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.15)
    rrect(ctx, -26, -44, 52, 88, 12)
    fill_stroke(ctx, hexc("2f2a44"), width=5)
    rrect(ctx, -18, -34, 36, 66, 6)
    glow = 0.75 + 0.25 * math.sin(t * 5)
    ctx.set_source_rgba(0.6 * glow, 0.85 * glow, 1 * glow, 1)
    ctx.fill()
    ctx.restore()


def storm(ctx, lt, x, y, t, strength=1.0):
    if strength <= 0.02:
        return
    ctx.push_group()
    dx = math.sin(t * 1.3) * 12
    puff(ctx, x + dx, y, 95, hexc("6b6f86"))
    flash = (t * 1.6) % 1.0 < 0.18
    if flash:
        ctx.move_to(x + dx + 10, y + 40)
        ctx.line_to(x + dx - 25, y + 120)
        ctx.line_to(x + dx + 5, y + 115)
        ctx.line_to(x + dx - 20, y + 190)
        ctx.line_to(x + dx + 40, y + 95)
        ctx.line_to(x + dx + 10, y + 100)
        ctx.line_to(x + dx + 30, y + 40)
        ctx.close_path()
        fill_stroke(ctx, hexc("ffe14d"), width=5)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(clamp(strength))


def rain_cloud(ctx, lt, x, y, t):
    a = clamp(lt * 2)
    ctx.push_group()
    puff(ctx, x, y, 48, hexc("9aa3b5"), width=5)
    ctx.set_source_rgba(0.5, 0.7, 1, 0.9)
    ctx.set_line_width(5)
    ctx.set_line_cap(1)
    for k in range(4):
        dy = (t * 140 + k * 23) % 70
        ctx.move_to(x - 36 + k * 24, y + 30 + dy)
        ctx.line_to(x - 40 + k * 24, y + 44 + dy)
        ctx.stroke()
    ctx.set_line_cap(0)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def bubble(ctx, lt, x, y, kind="thought", content="?", tail_to=None):
    """Thought or speech bubble with a symbol or short word inside."""
    s = ease_out_back(min(1, lt * 3))
    if s <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if kind == "thought":
        puff(ctx, 0, 0, 62, WHITE)
        if tail_to:
            tx, ty = tail_to[0] - x, tail_to[1] - y
            for i, r in enumerate((16, 10)):
                ellipse(ctx, tx * (0.45 + 0.25 * i), ty * (0.45 + 0.25 * i), r, r)
                fill_stroke(ctx, WHITE, width=5)
    else:
        rrect(ctx, -110, -60, 220, 120, 40)
        if tail_to:
            tx, ty = tail_to[0] - x, tail_to[1] - y
            ctx.move_to(-20, 55)
            ctx.line_to(tx * 0.6, ty * 0.6)
            ctx.line_to(25, 55)
        fill_stroke(ctx, WHITE)
    if content == "heart":
        heart(ctx, 0, 4, 30)
        fill_stroke(ctx, PINK, width=5)
    elif content == "dots":
        for i in range(3):
            on = int(lt * 4) % 3 >= i
            ellipse(ctx, -40 + i * 40, 0, 11, 11)
            ctx.set_source_rgba(*OUTLINE[:3], 1 if on else 0.3)
            ctx.fill()
    elif content:
        text(ctx, content, 0, 2, 54, hexc("ff8fab"))
    ctx.restore()


def floating_marks(ctx, lt, x, y, mark="?", color="ffd166"):
    for k in range(3):
        age = lt - k * 0.35
        if age < 0:
            continue
        a = clamp(1 - (age % 1.6) / 1.6)
        yy = y - (age % 1.6) * 60
        ctx.save()
        ctx.translate(x + (k - 1) * 46, yy)
        ctx.rotate((k - 1) * 0.25)
        ctx.push_group()
        text(ctx, mark, 0, 0, 52, hexc(color))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        ctx.restore()


def sparkles(ctx, lt, x, y, spread=180, n=6):
    for k in range(n):
        ph = lt * 2.4 + k * 1.3
        a = max(0, math.sin(ph))
        if a <= 0:
            continue
        sx = x + math.cos(k * 2.4) * spread * (0.4 + 0.6 * ((k * 37) % 10) / 10)
        sy = y + math.sin(k * 1.9) * spread * 0.5
        r = 16 * a
        ctx.move_to(sx, sy - r)
        ctx.curve_to(sx, sy, sx, sy, sx + r, sy)
        ctx.curve_to(sx, sy, sx, sy, sx, sy + r)
        ctx.curve_to(sx, sy, sx, sy, sx - r, sy)
        ctx.curve_to(sx, sy, sx, sy, sx, sy - r)
        ctx.set_source_rgba(1, 0.95, 0.6, a)
        ctx.fill()


def polaroid(ctx, lt, x, y, rot, label, old=False, couple_colors=("ff9a8b", "b9a3f5")):
    s = ease_out_back(min(1, lt * 2.2))
    if s <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    rrect(ctx, -105, -120, 210, 240, 8)
    fill_stroke(ctx, WHITE)
    ctx.rectangle(-88, -103, 176, 160)
    ctx.set_source_rgba(*hexc("bfe3f5"))
    ctx.fill()
    for i, col in enumerate(couple_colors):
        cx = -36 + i * 72
        ellipse(ctx, cx, 20, 34, 30)
        fill_stroke(ctx, hexc(col), width=4)
        for e in (-1, 1):
            ellipse(ctx, cx + e * 10, 12, 3.5, 4.5)
            ctx.set_source_rgba(*OUTLINE)
            ctx.fill()
        if old:
            ellipse(ctx, cx, -12, 16, 9)
            fill_stroke(ctx, (0.9, 0.9, 0.92, 1), width=3)
    text(ctx, label, 0, 88, 30, hexc("ff8fab"))
    ctx.restore()


def magnifier(ctx, x, y):
    ctx.save()
    ctx.translate(x, y)
    ctx.set_source_rgba(*OUTLINE)
    ctx.set_line_width(16)
    ctx.set_line_cap(1)
    ctx.move_to(40, 40)
    ctx.line_to(85, 85)
    ctx.stroke()
    ctx.set_line_cap(0)
    ellipse(ctx, 0, 0, 55, 55)
    fill_stroke(ctx, (0.85, 0.95, 1, 0.45), width=10)
    ctx.restore()


def security_camera(ctx, x, y, t):
    swivel = math.sin(t * 0.9) * 0.35
    ctx.save()
    ctx.translate(x, y)
    rrect(ctx, -8, -60, 16, 60, 6)
    fill_stroke(ctx, hexc("d9d4e6"), width=5)
    ctx.rotate(swivel + 0.4)
    rrect(ctx, -70, -26, 110, 52, 14)
    fill_stroke(ctx, hexc("f2eef8"), width=6)
    ellipse(ctx, -70, 0, 16, 20)
    fill_stroke(ctx, hexc("3b2340"), width=4)
    on = (t * 1.5) % 1 < 0.5
    ellipse(ctx, 20, -10, 7, 7)
    ctx.set_source_rgba(1, 0.25, 0.3, 1 if on else 0.3)
    ctx.fill()
    ctx.restore()


def flash(ctx, lt, w, h):
    a = clamp(0.85 - lt * 3)
    if a > 0:
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.rectangle(0, 0, w, h)
        ctx.fill()
