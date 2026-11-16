"""Small pictures for the bubble over a speaker's head: the thing the line is about.
Each is drawn around (0, 0) inside roughly 150 x 110. A name not listed here is shown as text."""
import math

from shorts.cartoon.draw import ellipse, hexc, rrect

from .cast import INK, paint

OUTLINE = INK


def fill_stroke(ctx, fill, width=5):
    """Flat colour; the edge is the same colour a little darker (as on the cast)."""
    paint(ctx, fill, 2.5 if width else 0)


def text(ctx, s, x, y, size, color):
    from .stage import label

    surf, wide, high = label(s, size, color)
    ctx.set_source_surface(surf, x - wide / 2, y - high / 2)
    ctx.paint()

ICONS = {}


def icon(name):
    def deco(fn):
        ICONS[name] = fn
        return fn
    return deco


def _line(ctx, pts, width=6, color=OUTLINE):
    ctx.set_source_rgba(*color)
    ctx.set_line_width(width)
    ctx.set_line_cap(1)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    ctx.set_line_cap(0)


@icon("couch")
def _couch(ctx, lt):
    rrect(ctx, -62, -42, 124, 60, 16)
    fill_stroke(ctx, hexc("7fb2f0"), width=5)
    rrect(ctx, -56, 0, 112, 34, 10)
    fill_stroke(ctx, hexc("a8ccf7"), width=5)
    for side in (-1, 1):
        rrect(ctx, side * 66 - 15, -18, 30, 56, 12)
        fill_stroke(ctx, hexc("7fb2f0"), width=5)
        rrect(ctx, side * 48 - 5, 36, 10, 14, 3)
        fill_stroke(ctx, hexc("8a5a3b"), width=4)


@icon("armchair")
def _armchair(ctx, lt):
    buzz = math.sin(lt * 40) * 1.5
    ctx.save()
    ctx.translate(buzz, 0)
    rrect(ctx, -36, -52, 72, 76, 20)
    fill_stroke(ctx, hexc("b98ae0"), width=5)
    rrect(ctx, -34, 2, 68, 30, 10)
    fill_stroke(ctx, hexc("d5b4f0"), width=5)
    for side in (-1, 1):
        rrect(ctx, side * 44 - 13, -14, 26, 54, 11)
        fill_stroke(ctx, hexc("b98ae0"), width=5)
    ctx.restore()
    for side in (-1, 1):  # it hums
        for k in (0, 1):
            _line(ctx, [(side * (70 + k * 13), -30 + k * 4), (side * (70 + k * 13), 10 - k * 4)], 5, hexc("ffb347"))


@icon("money")
def _money(ctx, lt):
    for k in range(3):
        ctx.save()
        ctx.translate(-8 + k * 8, 12 - k * 14)
        ctx.rotate(-0.12 + k * 0.1)
        rrect(ctx, -58, -28, 116, 56, 8)
        fill_stroke(ctx, hexc("7ccf6e"), width=5)
        ellipse(ctx, 0, 0, 17, 17)
        fill_stroke(ctx, hexc("c4f0b4"), width=4)
        ctx.restore()


@icon("receipt")
def _receipt(ctx, lt):
    ctx.move_to(-38, -54)
    ctx.line_to(38, -54)
    ctx.line_to(38, 48)
    for k in range(4):
        ctx.line_to(38 - k * 19 - 9.5, 38)
        ctx.line_to(38 - (k + 1) * 19, 48)
    ctx.close_path()
    fill_stroke(ctx, (1, 1, 1, 1), width=5)
    for k, wd in enumerate((48, 36, 48, 28)):
        _line(ctx, [(-24, -36 + k * 17), (-24 + wd, -36 + k * 17)], 5, hexc("b9b3c4"))
    _line(ctx, [(-24, 24), (24, 24)], 7, hexc("e8436f"))


@icon("fries")
def _fries(ctx, lt):
    for k, (x, top) in enumerate(((-26, -46), (-12, -58), (2, -50), (16, -60), (28, -44))):
        rrect(ctx, x - 6, top, 12, 60, 4)
        fill_stroke(ctx, hexc("ffd166"), width=4)
    ctx.move_to(-40, -8)
    ctx.line_to(40, -8)
    ctx.line_to(30, 52)
    ctx.line_to(-30, 52)
    ctx.close_path()
    fill_stroke(ctx, hexc("e8503a"), width=5)


@icon("lobster")
def _lobster(ctx, lt):
    red = hexc("ef5d4a")
    snap = 0.25 + 0.2 * math.sin(lt * 8)
    for side in (-1, 1):
        _line(ctx, [(side * 14, -18), (side * 44, -38)], 9, red)
        for half in (-1, 1):  # claw
            ctx.save()
            ctx.translate(side * 50, -44)
            ctx.rotate(side * 0.6 + half * snap)
            ellipse(ctx, 0, -14, 9, 18)
            fill_stroke(ctx, red, width=4)
            ctx.restore()
        _line(ctx, [(side * 6, -30), (side * 16, -58)], 4)
        for k in range(3):
            _line(ctx, [(side * 18, -2 + k * 12), (side * 34, 4 + k * 13)], 5, red)
    for k, (y, r) in enumerate(((36, 12), (24, 15), (10, 18))):  # tail
        ellipse(ctx, 0, y, r, 10)
        fill_stroke(ctx, red, width=4)
    ellipse(ctx, 0, -14, 22, 26)
    fill_stroke(ctx, red, width=5)
    for side in (-1, 1):
        ellipse(ctx, side * 8, -26, 4, 5)
        ctx.set_source_rgba(*OUTLINE)
        ctx.fill()
    ellipse(ctx, 0, 50, 62, 9)
    fill_stroke(ctx, (1, 1, 1, 1), width=4)


@icon("steak")
def _steak(ctx, lt):
    ellipse(ctx, 0, 14, 72, 34)
    fill_stroke(ctx, (1, 1, 1, 1), width=5)
    ctx.move_to(-44, 4)
    ctx.curve_to(-52, -34, 0, -40, 22, -22)
    ctx.curve_to(52, -20, 56, 22, 22, 24)
    ctx.curve_to(-6, 34, -40, 30, -44, 4)
    ctx.close_path()
    fill_stroke(ctx, hexc("b5562b"), width=5)
    ellipse(ctx, 18, 2, 12, 9)
    fill_stroke(ctx, hexc("fff4e0"), width=4)
    for k in range(3):
        _line(ctx, [(-30 + k * 14, -12), (-22 + k * 14, 12)], 4, hexc("6b3a22"))
    for k in range(2):  # steam
        x = -10 + k * 26
        rise = (lt * 30 + k * 14) % 24
        ctx.set_source_rgba(0.6, 0.55, 0.6, 0.8 - rise / 30)
        ctx.set_line_width(4)
        ctx.move_to(x, -40 - rise)
        ctx.curve_to(x + 8, -48 - rise, x - 8, -54 - rise, x, -62 - rise)
        ctx.stroke()


@icon("wifi")
def _wifi(ctx, lt):
    on = int(lt * 3) % 4
    for k, r in enumerate((22, 44, 66)):
        ctx.set_source_rgba(*hexc("4a90e2", 1 if k < on else 0.25))
        ctx.set_line_width(11)
        ctx.set_line_cap(1)
        ctx.new_sub_path()
        ctx.arc(0, 36, r, math.pi * 1.25, math.pi * 1.75)
        ctx.stroke()
    ctx.set_line_cap(0)
    ellipse(ctx, 0, 36, 9, 9)
    ctx.set_source_rgba(*hexc("4a90e2"))
    ctx.fill()


@icon("lock")
def _lock(ctx, lt):
    ctx.set_source_rgba(*hexc("9a9fb0"))
    ctx.set_line_width(13)
    ctx.new_sub_path()
    ctx.arc(0, -16, 26, math.pi, 2 * math.pi)
    ctx.stroke()
    rrect(ctx, -42, -16, 84, 66, 12)
    fill_stroke(ctx, hexc("ffd166"), width=5)
    ellipse(ctx, 0, 10, 9, 9)
    ctx.set_source_rgba(*OUTLINE)
    ctx.fill()
    _line(ctx, [(0, 12), (0, 30)], 7)


@icon("tv")
def _tv(ctx, lt):
    rrect(ctx, -66, -46, 132, 84, 12)
    fill_stroke(ctx, hexc("2f2a44"), width=5)
    rrect(ctx, -56, -36, 112, 64, 6)
    ctx.set_source_rgba(*hexc("3d4f8f"))
    ctx.fill()
    for k in range(8):  # the loading wheel of a frozen stream
        a = k * math.pi / 4
        lit = (int(lt * 8) - k) % 8
        ellipse(ctx, math.cos(a) * 18, -4 + math.sin(a) * 18, 5, 5)
        ctx.set_source_rgba(1, 1, 1, 1 - lit * 0.11)
        ctx.fill()
    _line(ctx, [(-24, 50), (24, 50)], 8)
    _line(ctx, [(0, 38), (0, 50)], 8)


@icon("bingo")
def _bingo(ctx, lt):
    for k, (x, y, col, n) in enumerate(((-36, 8, "ff6f9c", "7"), (34, 14, "7fb2f0", "22"), (0, -24, "ffd166", "B"))):
        bob = math.sin(lt * 4 + k * 2) * 3
        ellipse(ctx, x, y + bob, 30, 30)
        fill_stroke(ctx, hexc(col), width=5)
        ellipse(ctx, x, y + bob, 17, 17)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.fill()
        text(ctx, n, x, y + bob, 22, "2b2d42")


def draw(ctx, name, lt):
    if name in ICONS:
        ICONS[name](ctx, lt)
    else:
        text(ctx, name, 0, 0, 84 if len(name) <= 2 else 60 if len(name) <= 4 else 40, "e63946")
