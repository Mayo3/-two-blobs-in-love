"""Backgrounds. The static part is painted once and cached; small things move each frame."""
import math
import random

import cairo

from .draw import OUTLINE, cloud, ellipse, fill_stroke, heart, hexc, mix, puff, rrect

W, H = 1080, 1920
GROUND = 1660


def vgrad(ctx, y0, y1, c0, c1):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *hexc(c0))
    g.add_color_stop_rgba(1, *hexc(c1))
    return g


class Scene:
    kinds = ("home", "park", "lab", "night")

    def __init__(self, kind):
        assert kind in self.kinds, kind
        self.kind = kind
        self.rng = random.Random(7)
        self.static = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(self.static)
        getattr(self, f"_static_{kind}")(ctx)
        # colour of the bottom edge, used to fill below the lifted stage
        self.static.flush()
        px = bytes(self.static.get_data()[(H - 1) * self.static.get_stride() + 540 * 4:][:4])
        self.floor = (px[2] / 255, px[1] / 255, px[0] / 255, 1)
        self.stars = [(self.rng.uniform(0, W), self.rng.uniform(0, 1300), self.rng.uniform(2, 5), self.rng.uniform(0, 6)) for _ in range(70)]

    def draw(self, ctx, t, anim):
        ctx.set_source_surface(self.static, 0, 0)
        ctx.paint()
        getattr(self, f"_live_{self.kind}")(ctx, t, anim)

    # ---------- home ----------
    def _static_home(self, ctx):
        ctx.set_source(vgrad(ctx, 0, 1560, "c97f8f", "9e5a73"))
        ctx.paint()
        ctx.set_source_rgba(1, 1, 1, 0.06)
        for y in range(40, 1560, 90):
            for x in range(40 + (y // 90 % 2) * 45, W, 90):
                ellipse(ctx, x, y, 9, 9)
                ctx.fill()
        # window
        rrect(ctx, 230, 330, 620, 500, 30)
        ctx.set_source(vgrad(ctx, 330, 830, "ffd3a1", "ff9fa8"))
        ctx.fill_preserve()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(8)
        ctx.stroke()
        ctx.move_to(230, 700)
        ctx.curve_to(400, 600, 560, 720, 850, 640)
        ctx.line_to(850, 800)
        ctx.line_to(230, 800)
        ctx.close_path()
        ctx.set_source_rgba(*hexc("e88a8f", 0.7))
        ctx.fill()
        # curtains
        for side in (-1, 1):
            x0 = 230 if side < 0 else 850
            ctx.move_to(x0 - side * 30, 300)
            ctx.curve_to(x0 + side * 90, 420, x0 - side * 10, 650, x0 + side * 60, 870)
            ctx.line_to(x0 - side * 70, 870)
            ctx.line_to(x0 - side * 70, 300)
            ctx.close_path()
            fill_stroke(ctx, hexc("f7a8b8"))
        rrect(ctx, 180, 286, 720, 30, 15)
        fill_stroke(ctx, hexc("f3d9b1"))
        # picture frame
        rrect(ctx, 860, 1180, 120, 140, 10)
        fill_stroke(ctx, hexc("f3d9b1"))
        heart(ctx, 920, 1255, 30)
        fill_stroke(ctx, hexc("ff5d8f"), width=5)
        # floor and rug
        ctx.rectangle(0, 1560, W, H - 1560)
        ctx.set_source(vgrad(ctx, 1560, H, "b97a5a", "8a5440"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1560)
        ctx.line_to(W, 1560)
        ctx.stroke()
        ellipse(ctx, 540, 1670, 400, 70)
        fill_stroke(ctx, hexc("f2c14e"))
        ellipse(ctx, 540, 1670, 300, 48)
        ctx.set_source_rgba(1, 1, 1, 0.25)
        ctx.set_line_width(8)
        ctx.stroke()
        # lamp
        rrect(ctx, 965, 1330, 12, 240, 6)
        fill_stroke(ctx, hexc("f3d9b1"), width=5)
        ctx.move_to(920, 1340)
        ctx.line_to(1020, 1340)
        ctx.line_to(995, 1270)
        ctx.line_to(945, 1270)
        ctx.close_path()
        fill_stroke(ctx, hexc("ffe3a3"))

    def _live_home(self, ctx, t, anim):
        ctx.save()
        rrect(ctx, 234, 334, 612, 492, 26)
        ctx.clip()
        for i, (y, s, sp) in enumerate(((430, 50, 18), (520, 36, 11), (390, 30, 25))):
            x = (t * sp + i * 300) % 900 - 100 + 230
            cloud(ctx, x, y, s)
            ctx.set_source_rgba(1, 1, 1, 0.9)
            ctx.fill()
        ctx.restore()
        # window cross
        ctx.set_source_rgba(*hexc("f3d9b1"))
        ctx.rectangle(534, 330, 12, 500)
        ctx.rectangle(230, 574, 620, 12)
        ctx.fill()
        # lamp glow
        ctx.set_source_rgba(1, 0.9, 0.6, 0.12 + 0.03 * math.sin(t * 2))
        ellipse(ctx, 970, 1330, 140, 120)
        ctx.fill()
        self._plant(ctx, 110, 1560, t)

    def _plant(self, ctx, x, y, t):
        sway = math.sin(t * 1.4) * 0.08
        for i, (ang, ln) in enumerate(((-0.6, 150), (-0.2, 190), (0.25, 170), (0.65, 130))):
            ctx.save()
            ctx.translate(x, y - 60)
            ctx.rotate(ang + sway * (1 + i * 0.3))
            ellipse(ctx, 0, -ln / 2, 26, ln / 2)
            fill_stroke(ctx, hexc("6cc070"), width=5)
            ctx.restore()
        rrect(ctx, x - 55, y - 80, 110, 90, 16)
        fill_stroke(ctx, hexc("e07a5f"))

    # ---------- park ----------
    def _static_park(self, ctx):
        ctx.set_source(vgrad(ctx, 0, 1500, "6fa8dc", "bfe3f5"))
        ctx.paint()
        for y0, col in ((1420, "a8dc93"), (1500, "86c97a")):
            ctx.move_to(0, y0)
            ctx.curve_to(300, y0 - 120, 650, y0 + 40, W, y0 - 80)
            ctx.line_to(W, H)
            ctx.line_to(0, H)
            ctx.close_path()
            fill_stroke(ctx, hexc(col))
        ctx.rectangle(0, 1590, W, H - 1590)
        ctx.set_source(vgrad(ctx, 1590, H, "6cbb63", "4f9a4c"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1590)
        ctx.curve_to(400, 1570, 700, 1600, W, 1585)
        ctx.stroke()

    def _live_park(self, ctx, t, anim):
        # sun
        ctx.save()
        ctx.translate(900, 330)
        ctx.rotate(t * 0.25)
        for k in range(10):
            ctx.rotate(math.pi / 5)
            rrect(ctx, -9, 95, 18, 45, 9)
            ctx.set_source_rgba(*hexc("ffd166"))
            ctx.fill()
        ctx.restore()
        ellipse(ctx, 900, 330, 80, 80)
        fill_stroke(ctx, hexc("ffd166"))
        for i, (y, s, sp) in enumerate(((420, 60, 14), (760, 44, 9), (300, 38, 20))):
            x = (t * sp + i * 420) % 1400 - 160
            puff(ctx, x, y, s, (1, 1, 1, 0.95), width=5)
        for x in (110, 975):
            self._tree(ctx, x, 1600, t)
        for k in range(9):
            fx = 60 + k * 120 + (k % 2) * 30
            sway = math.sin(t * 2 + k) * 6
            ctx.set_source_rgba(*hexc("3f8a3f"))
            ctx.set_line_width(5)
            ctx.move_to(fx, 1700)
            ctx.line_to(fx + sway, 1655)
            ctx.stroke()
            for p in range(5):
                a = p / 5 * 2 * math.pi
                ellipse(ctx, fx + sway + math.cos(a) * 12, 1650 + math.sin(a) * 12, 9, 9)
                ctx.set_source_rgba(*hexc(("ffffff", "ffd166", "ff8fab")[k % 3]))
                ctx.fill()
            ellipse(ctx, fx + sway, 1650, 7, 7)
            ctx.set_source_rgba(*hexc("ff8c42"))
            ctx.fill()

    def _tree(self, ctx, x, y, t):
        rrect(ctx, x - 18, y - 260, 36, 260, 14)
        fill_stroke(ctx, hexc("9c6b4e"))
        sway = math.sin(t * 1.1 + x) * 5
        for dx, dy, r in ((0, -330, 110), (-70, -270, 80), (70, -270, 80)):
            ellipse(ctx, x + dx + sway, y + dy, r, r)
            fill_stroke(ctx, hexc("5fb85c"))

    # ---------- lab ----------
    def _static_lab(self, ctx):
        ctx.set_source(vgrad(ctx, 0, 1580, "8fb6cf", "5f8aa8"))
        ctx.paint()
        ctx.set_source_rgba(1, 1, 1, 0.08)
        ctx.set_line_width(3)
        for x in range(0, W, 120):
            ctx.move_to(x, 0)
            ctx.line_to(x, 1580)
        for y in range(0, 1580, 120):
            ctx.move_to(0, y)
            ctx.line_to(W, y)
        ctx.stroke()
        ctx.rectangle(0, 1580, W, H - 1580)
        ctx.set_source(vgrad(ctx, 1580, H, "4f7896", "3c5f7a"))
        ctx.fill()
        # scanner ring behind the couple
        ctx.new_path()
        ctx.arc(540, 1450, 330, 0, 2 * math.pi)
        ctx.new_sub_path()
        ctx.arc_negative(540, 1450, 235, 2 * math.pi, 0)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        fill_stroke(ctx, hexc("eef3f8"))
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        # shelf with flasks
        rrect(ctx, 30, 1240, 170, 18, 8)
        fill_stroke(ctx, hexc("f3d9b1"), width=5)
        for i, col in enumerate(("ff8fab", "7ccf6e", "ffd166")):
            fx = 60 + i * 55
            ctx.move_to(fx - 8, 1170)
            ctx.line_to(fx - 8, 1195)
            ctx.line_to(fx - 22, 1236)
            ctx.line_to(fx + 22, 1236)
            ctx.line_to(fx + 8, 1195)
            ctx.line_to(fx + 8, 1170)
            ctx.close_path()
            fill_stroke(ctx, hexc(col), width=5)

    def _live_lab(self, ctx, t, anim):
        for k in range(8):
            ang = k / 8 * 2 * math.pi
            on = (t * 2 + k) % 3 < 1
            ellipse(ctx, 540 + math.cos(ang) * 282, 1450 + math.sin(ang) * 282, 9, 9)
            ctx.set_source_rgba(*(hexc("7ccf6e") if anim.monitor < 0.5 else hexc("ff6b6b"))[:3], 1 if on else 0.35)
            ctx.fill()
        # monitor with brain threat meter
        mx, my = 850, 1200
        rrect(ctx, mx - 8, my + 60, 16, 140, 6)
        fill_stroke(ctx, hexc("d9d4e6"), width=5)
        rrect(ctx, mx - 120, my - 85, 240, 160, 18)
        fill_stroke(ctx, hexc("2f2a44"))
        level = anim.monitor
        col = mix(hexc("7ccf6e"), hexc("ff6b6b"), level)
        ctx.set_source_rgba(*col)
        ctx.set_line_width(6)
        for i in range(0, 200, 4):
            x = mx - 100 + i
            y = my + 10 + math.sin(i * 0.15 + t * 10) * (6 + 40 * level) * math.sin(i / 200 * math.pi)
            if i == 0:
                ctx.move_to(x, y)
            else:
                ctx.line_to(x, y)
        ctx.stroke()
        # tiny brain icon
        for dx in (-14, 14):
            ellipse(ctx, mx - 80 + dx * 0.6, my - 52, 16, 12)
            fill_stroke(ctx, (*col[:3], 1), width=3)
        for k in range(3):
            by = (t * 50 + k * 30) % 70
            ellipse(ctx, 60 + k * 55 + math.sin(t * 3 + k) * 4, 1225 - by, 5, 5)
            ctx.set_source_rgba(1, 1, 1, 0.6 * (1 - by / 70))
            ctx.fill()

    # ---------- night ----------
    def _static_night(self, ctx):
        ctx.set_source(vgrad(ctx, 0, 1500, "1f2150", "4b3a78"))
        ctx.paint()
        ellipse(ctx, 830, 380, 85, 85)
        fill_stroke(ctx, hexc("fff1c1"))
        ellipse(ctx, 800, 360, 18, 14)
        ctx.set_source_rgba(0.9, 0.85, 0.7, 0.6)
        ctx.fill()
        for y0, col in ((1430, "3b4a7a"), (1520, "2e3a63")):
            ctx.move_to(0, y0)
            ctx.curve_to(350, y0 - 110, 700, y0 + 40, W, y0 - 60)
            ctx.line_to(W, H)
            ctx.line_to(0, H)
            ctx.close_path()
            fill_stroke(ctx, hexc(col))
        ctx.rectangle(0, 1600, W, H - 1600)
        ctx.set_source_rgba(*hexc("27325a"))
        ctx.fill()

    def _live_night(self, ctx, t, anim):
        for x, y, r, ph in self.stars:
            a = 0.4 + 0.6 * abs(math.sin(t * 1.5 + ph))
            ellipse(ctx, x, y, r, r)
            ctx.set_source_rgba(1, 0.97, 0.85, a)
            ctx.fill()
        for k in range(7):
            fx = (k * 157 + math.sin(t * 0.7 + k) * 40) % W
            fy = 1450 + math.sin(t * 1.1 + k * 2) * 60
            ctx.set_source_rgba(1, 0.95, 0.5, 0.5 + 0.5 * math.sin(t * 4 + k))
            ellipse(ctx, fx, fy, 6, 6)
            ctx.fill()
