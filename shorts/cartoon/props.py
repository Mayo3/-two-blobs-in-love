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


def tshirt(ctx, x, y, s=1.0, color="f6f1ea"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.new_path()
    for px, py in ((-34, -52), (-78, -30), (-62, 4), (-42, -6), (-42, 58), (42, 58), (42, -6), (62, 4), (78, -30), (34, -52)):
        ctx.line_to(px, py)
    ctx.curve_to(20, -36, -20, -36, -34, -52)
    ctx.close_path()
    fill_stroke(ctx, hexc(color), width=5)
    ctx.restore()


def scent(ctx, lt, x, y, color="9be3b0", n=3):
    """Wavy wisps drifting up from (x, y)."""
    ctx.set_line_width(7)
    ctx.set_line_cap(1)
    for k in range(n):
        age = (lt * 0.8 + k / n) % 1.0
        ox = x + (k - (n - 1) / 2) * 34
        ctx.new_path()
        for i in range(9):
            yy = y - age * 150 - i * 9
            ctx.line_to(ox + math.sin(i * 0.9 + lt * 4 + k) * 10, yy)
        ctx.set_source_rgba(*hexc(color)[:3], 0.9 * math.sin(math.pi * age))
        ctx.stroke()
    ctx.set_line_cap(0)


def message(ctx, x, y, s, mine, content="dots"):
    """A chat bubble the size of a thumb: `mine` picks the side its tail is on and its colour."""
    if s <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rrect(ctx, -50, -30, 100, 60, 26)
    ctx.move_to(30 if mine else -30, 26)
    ctx.line_to(46 if mine else -46, 46)
    ctx.line_to(12 if mine else -12, 28)
    fill_stroke(ctx, hexc("8fd3ff") if mine else WHITE, width=5)
    if content == "heart":
        heart(ctx, 0, 3, 17)
        fill_stroke(ctx, PINK, width=4)
    else:
        for i in range(3):
            ellipse(ctx, -22 + i * 22, 0, 6, 6)
            ctx.set_source_rgba(*OUTLINE)
            ctx.fill()
    ctx.restore()


def pulse(lt, rate=1.15):
    """0..1 double thump of a heartbeat."""
    ph = (lt * rate) % 1.0
    return max(0.0, math.sin(ph * math.pi * 6)) * (1 if ph < 0.34 else 0) * (1 - ph)


def pulse_line(ctx, lt, x0, x1, y, color="ff5d8f"):
    """A heart-monitor line that draws itself from x0 to x1 over and over."""
    head = (lt * 0.9) % 1.3
    ctx.set_line_width(8)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    ctx.new_path()
    n = 60
    for i in range(n + 1):
        f = i / n
        if f > head:
            break
        ph = (f * 3) % 1.0
        dy = -70 if 0.42 < ph < 0.5 else 46 if 0.5 <= ph < 0.58 else -18 if 0.58 <= ph < 0.64 else 0
        ctx.line_to(x0 + (x1 - x0) * f, y + dy)
    ctx.set_source_rgba(*hexc(color))
    ctx.stroke()
    ctx.set_line_cap(0)
    ctx.set_line_join(0)


def date_table(ctx, x, ground, t):
    """A little round table with a cloth and a candle."""
    rrect(ctx, x - 10, ground - 150, 20, 150, 6)
    fill_stroke(ctx, hexc("8a5a44"), width=5)
    ellipse(ctx, x, ground - 4, 58, 12)
    fill_stroke(ctx, hexc("8a5a44"), width=5)
    ellipse(ctx, x, ground - 156, 120, 26)
    fill_stroke(ctx, hexc("fff4e6"), width=6)
    rrect(ctx, x - 9, ground - 232, 18, 70, 5)
    fill_stroke(ctx, hexc("ffe9a8"), width=5)
    f = 1 + 0.12 * math.sin(t * 13) + 0.08 * math.sin(t * 7.3)
    ctx.set_source_rgba(1, 0.75, 0.3, 0.25)
    ellipse(ctx, x, ground - 256, 46 * f, 46 * f)
    ctx.fill()
    ctx.new_path()
    ctx.move_to(x, ground - 232)
    ctx.curve_to(x - 20 * f, ground - 250, x - 6, ground - 272, x + 2 * math.sin(t * 9), ground - 232 - 54 * f)
    ctx.curve_to(x + 8, ground - 270, x + 20 * f, ground - 250, x, ground - 232)
    fill_stroke(ctx, hexc("ffb347"), width=4)


def ring(ctx, lt, x, y):
    s = ease_out_back(min(1, lt * 2.4))
    if s <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y + math.sin(lt * 2.4) * 8)
    ctx.scale(s, s)
    ctx.new_path()
    ctx.arc(0, 30, 52, 0, 2 * math.pi)
    ctx.set_source_rgba(*OUTLINE)
    ctx.set_line_width(30)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*hexc("ffd166"))
    ctx.set_line_width(18)
    ctx.stroke()
    ctx.new_path()
    for px, py in ((-44, -52), (-24, -80), (24, -80), (44, -52), (0, -8)):
        ctx.line_to(px, py)
    ctx.close_path()
    fill_stroke(ctx, hexc("bfefff"), width=6)
    ctx.move_to(-44, -52)
    ctx.line_to(44, -52)
    ctx.set_source_rgba(*OUTLINE)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()


def brain(ctx, lt, x, y):
    s = ease_out_back(min(1, lt * 2.4)) * (1 + 0.04 * math.sin(lt * 6))
    if s <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    glow = 0.5 + 0.5 * math.sin(lt * 5)
    ctx.set_source_rgba(1, 0.85, 0.4, 0.18 + 0.22 * glow)
    ellipse(ctx, 0, 0, 150, 120)
    ctx.fill()
    puff(ctx, 0, 0, 78, hexc("ffb3c7"))
    ctx.set_source_rgba(*hexc("e0708f"))
    ctx.set_line_width(7)
    ctx.set_line_cap(1)
    ctx.move_to(0, -52)
    ctx.curve_to(-14, -20, 14, 0, 0, 44)
    ctx.stroke()
    for sx in (-1, 1):
        ctx.move_to(sx * 20, -24)
        ctx.curve_to(sx * 46, -40, sx * 56, -6, sx * 34, 6)
        ctx.stroke()
        ctx.move_to(sx * 22, 26)
        ctx.curve_to(sx * 44, 14, sx * 62, 30, sx * 50, 40)
        ctx.stroke()
    ctx.set_line_cap(0)
    ctx.restore()


def dashed_arc(ctx, lt, x0, x1, y, rise=150):
    """A dashed path between two far-apart points, with a small heart travelling along it."""
    ctx.set_source_rgba(1, 1, 1, 0.85)
    ctx.set_line_width(7)
    ctx.set_line_cap(1)
    ctx.set_dash([4, 26], -lt * 40)
    ctx.move_to(x0, y)
    ctx.curve_to(x0 + (x1 - x0) * 0.25, y - rise, x0 + (x1 - x0) * 0.75, y - rise, x1, y)
    ctx.stroke()
    ctx.set_dash([])
    ctx.set_line_cap(0)
    f = (lt * 0.45) % 1.0
    hx = x0 + (x1 - x0) * f
    hy = y - rise * 3 * f * (1 - f)
    heart(ctx, hx, hy, 24)
    fill_stroke(ctx, PINK, width=5)
