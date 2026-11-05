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
    # Each has its own dominant colour so they stay different as thumbnails on the profile feed.
    # The zoomed stage only shows about x 100-980, y 560 and down, so keep key details in there.
    kinds = ("home", "park", "lab", "night", "cafe", "beach", "kitchen", "rain", "snow", "autumn")

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
        ctx.translate(270, 770)
        ctx.rotate(t * 0.25)
        for k in range(10):
            ctx.rotate(math.pi / 5)
            rrect(ctx, -9, 95, 18, 45, 9)
            ctx.set_source_rgba(*hexc("ffd166"))
            ctx.fill()
        ctx.restore()
        ellipse(ctx, 270, 770, 80, 80)
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
        ellipse(ctx, 770, 800, 85, 85)
        fill_stroke(ctx, hexc("fff1c1"))
        ellipse(ctx, 740, 780, 18, 14)
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

    # ---------- cafe ----------
    def _static_cafe(self, ctx):
        ctx.set_source(vgrad(ctx, 500, 1400, "b67a45", "8a5430"))
        ctx.paint()
        # chalkboard
        rrect(ctx, 140, 640, 340, 290, 14)
        fill_stroke(ctx, hexc("2f3a36"), width=12, outline=hexc("e0b27a"))
        heart(ctx, 310, 760, 62)
        fill_stroke(ctx, hexc("ff8fab"), width=0)
        ctx.set_source_rgba(1, 1, 1, 0.75)
        for y, w in ((840, 200), (875, 140)):
            rrect(ctx, 310 - w / 2, y, w, 10, 5)
            ctx.fill()
        # window with a warm evening outside
        rrect(ctx, 610, 620, 320, 420, 22)
        ctx.set_source(vgrad(ctx, 620, 1040, "ffe2ab", "ff9f6e"))
        ctx.fill_preserve()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(10)
        ctx.stroke()
        ctx.move_to(770, 620)
        ctx.line_to(770, 1040)
        ctx.move_to(610, 830)
        ctx.line_to(930, 830)
        ctx.set_line_width(8)
        ctx.stroke()
        # shelf with mugs
        rrect(ctx, 140, 1090, 340, 18, 8)
        fill_stroke(ctx, hexc("e0b27a"), width=5)
        for i, col in enumerate(("ff8fab", "fff4e0", "7cc8d8", "ffd166")):
            x = 170 + i * 78
            ctx.new_path()
            ctx.arc(x + 50, 1060, 14, -math.pi / 2, math.pi / 2)
            ctx.set_source_rgba(*OUTLINE)
            ctx.set_line_width(7)
            ctx.stroke()
            rrect(ctx, x, 1030, 50, 60, 8)
            fill_stroke(ctx, hexc(col), width=5)
        # counter, with the couple standing in front of it
        ctx.rectangle(0, 1420, W, 180)
        fill_stroke(ctx, hexc("5a3320"))
        ctx.set_source_rgba(1, 1, 1, 0.07)
        for x in range(60, W, 150):
            rrect(ctx, x, 1445, 110, 130, 10)
            ctx.fill()
        rrect(ctx, -20, 1385, W + 40, 40, 12)
        fill_stroke(ctx, hexc("efd3aa"))
        # espresso machine
        rrect(ctx, 830, 1230, 150, 155, 16)
        fill_stroke(ctx, hexc("d5dbe0"))
        rrect(ctx, 860, 1260, 90, 34, 8)
        fill_stroke(ctx, hexc("3b2340"), width=4)
        # floor
        ctx.rectangle(0, 1590, W, H - 1590)
        ctx.set_source(vgrad(ctx, 1590, H, "7c4e2f", "5e3923"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1590)
        ctx.line_to(W, 1590)
        ctx.stroke()

    def _live_cafe(self, ctx, t, anim):
        # pendant lamp, swaying gently
        x = 545 + math.sin(t * 0.9) * 10
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(545, 500)
        ctx.line_to(x, 690)
        ctx.stroke()
        ctx.set_source_rgba(1, 0.86, 0.5, 0.2 + 0.03 * math.sin(t * 2))
        ellipse(ctx, x, 770, 150, 130)
        ctx.fill()
        ctx.move_to(x - 62, 760)
        ctx.curve_to(x - 50, 690, x + 50, 690, x + 62, 760)
        ctx.close_path()
        fill_stroke(ctx, hexc("3f8f7f"))
        ellipse(ctx, x, 766, 20, 12)
        ctx.set_source_rgba(*hexc("fff1c1"))
        ctx.fill()
        # steaming cup on the counter
        for k in range(3):
            rise = (t * 34 + k * 30) % 90
            ellipse(ctx, 540 + math.sin(t * 2 + k * 2 + rise * 0.05) * 9, 1335 - rise, 8 + rise * 0.07, 8 + rise * 0.07)
            ctx.set_source_rgba(1, 1, 1, 0.5 * (1 - rise / 90))
            ctx.fill()
        rrect(ctx, 510, 1340, 60, 46, 8)
        fill_stroke(ctx, hexc("fff4e0"), width=5)

    # ---------- beach ----------
    def _static_beach(self, ctx):
        ctx.set_source(vgrad(ctx, 500, 1220, "3fd0d8", "c9f6e6"))
        ctx.paint()
        ctx.rectangle(0, 1220, W, 260)
        ctx.set_source(vgrad(ctx, 1220, 1480, "0f9fb5", "4fd6c8"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1220)
        ctx.line_to(W, 1220)
        ctx.stroke()
        # sand
        ctx.move_to(0, 1490)
        ctx.curve_to(300, 1440, 700, 1530, W, 1470)
        ctx.line_to(W, H)
        ctx.line_to(0, H)
        ctx.close_path()
        ctx.set_source(vgrad(ctx, 1450, H, "ffe39a", "efc06a"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1490)
        ctx.curve_to(300, 1440, 700, 1530, W, 1470)
        ctx.stroke()
        # sandcastle
        for x, y, w, h in ((840, 1490, 150, 110), (870, 1440, 40, 50), (930, 1440, 40, 50)):
            rrect(ctx, x, y, w, h, 8)
            fill_stroke(ctx, hexc("f2c777"), width=5)
        # striped umbrella
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(10)
        ctx.move_to(190, 1650)
        ctx.line_to(190, 1180)
        ctx.stroke()
        for i, col in enumerate(("ff5d6c", "fff4e0", "ff5d6c", "fff4e0", "ff5d6c")):
            a0, a1 = math.pi + i * math.pi / 5, math.pi + (i + 1) * math.pi / 5
            ctx.move_to(190, 1200)
            ctx.arc(190, 1200, 150, a0, a1)
            ctx.close_path()
            fill_stroke(ctx, hexc(col), width=5)

    def _live_beach(self, ctx, t, anim):
        ctx.save()
        ctx.translate(800, 760)
        ctx.rotate(t * 0.25)
        for k in range(10):
            ctx.rotate(math.pi / 5)
            rrect(ctx, -9, 90, 18, 42, 9)
            ctx.set_source_rgba(*hexc("ffc93c"))
            ctx.fill()
        ctx.restore()
        ellipse(ctx, 800, 760, 76, 76)
        fill_stroke(ctx, hexc("ffc93c"))
        for i, (y, s, sp) in enumerate(((680, 52, 12), (980, 40, 8))):
            x = (t * sp + i * 520) % 1300 - 110
            puff(ctx, x, y, s, (1, 1, 1, 0.95), width=5)
        # gulls
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(5)
        for i, (x0, y0) in enumerate(((330, 900), (440, 840))):
            x = x0 + math.sin(t * 0.4 + i) * 50
            flap = math.sin(t * 5 + i) * 10
            ctx.move_to(x - 30, y0 - flap)
            ctx.curve_to(x - 15, y0 - 16, x - 5, y0 - 8, x, y0)
            ctx.curve_to(x + 5, y0 - 8, x + 15, y0 - 16, x + 30, y0 - flap)
            ctx.stroke()
        # waves rolling on the sea
        ctx.set_source_rgba(1, 1, 1, 0.65)
        ctx.set_line_width(7)
        for row, y in enumerate((1275, 1345, 1415)):
            for k in range(5):
                x = (k * 260 + t * (22 + row * 10) + row * 90) % (W + 200) - 100
                ctx.move_to(x - 45, y)
                ctx.curve_to(x - 20, y - 16, x + 20, y + 16, x + 45, y)
                ctx.stroke()

    # ---------- kitchen ----------
    def _static_kitchen(self, ctx):
        ctx.set_source(vgrad(ctx, 500, 1400, "ffe07a", "ffc94d"))
        ctx.paint()
        # upper cabinets
        for x in (110, 400, 690):
            rrect(ctx, x, 590, 280, 330, 14)
            fill_stroke(ctx, hexc("35a79c"))
            rrect(ctx, x + 28, 620, 224, 270, 10)
            ctx.set_source_rgba(1, 1, 1, 0.13)
            ctx.fill()
            ellipse(ctx, x + 240, 860, 11, 11)
            fill_stroke(ctx, hexc("fff4e0"), width=4)
        # white tiled splashback
        ctx.rectangle(0, 1070, W, 320)
        ctx.set_source_rgba(*hexc("fffaf0"))
        ctx.fill()
        ctx.set_source_rgba(*hexc("e5c98f"))
        ctx.set_line_width(3)
        for y in range(1070, 1390, 64):
            ctx.move_to(0, y)
            ctx.line_to(W, y)
            for x in range(32 * (((y - 1070) // 64) % 2), W, 64):
                ctx.move_to(x, y)
                ctx.line_to(x, y + 64)
        ctx.stroke()
        # hanging utensils
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(8)
        ctx.move_to(130, 1100)
        ctx.line_to(420, 1100)
        ctx.stroke()
        for x, col in ((190, "e8634f"), (340, "f2a03d")):
            rrect(ctx, x - 7, 1100, 14, 70, 6)
            fill_stroke(ctx, hexc("8a5a3b"), width=4)
            ellipse(ctx, x, 1205, 44, 44)
            fill_stroke(ctx, hexc(col))
        # worktop and lower cabinets
        ctx.rectangle(0, 1420, W, 180)
        fill_stroke(ctx, hexc("35a79c"))
        ctx.set_source_rgba(1, 1, 1, 0.13)
        for x in range(50, W, 200):
            rrect(ctx, x, 1445, 170, 130, 10)
            ctx.fill()
        rrect(ctx, -20, 1385, W + 40, 40, 12)
        fill_stroke(ctx, hexc("fff4e0"))
        # floor
        ctx.rectangle(0, 1590, W, H - 1590)
        ctx.set_source(vgrad(ctx, 1590, H, "d98e5a", "b96f42"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1590)
        ctx.line_to(W, 1590)
        ctx.stroke()

    def _live_kitchen(self, ctx, t, anim):
        # wall clock, between the cabinets and the tiles
        ellipse(ctx, 540, 1000, 56, 56)
        fill_stroke(ctx, hexc("fff4e0"))
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        for ang, ln in ((t * 0.9, 42), (t * 0.075, 28)):
            ctx.move_to(540, 1000)
            ctx.line_to(540 + math.sin(ang) * ln, 1000 - math.cos(ang) * ln)
            ctx.stroke()
        # kettle on the worktop, steaming
        for k in range(4):
            rise = (t * 60 + k * 35) % 140
            ellipse(ctx, 905 + rise * 0.15 + math.sin(t * 3 + k + rise * 0.05) * 10, 1225 - rise, 10 + rise * 0.1, 10 + rise * 0.1)
            ctx.set_source_rgba(0.75, 0.72, 0.68, 0.65 * (1 - rise / 140))
            ctx.fill()
        ctx.new_path()
        ctx.arc(855, 1290, 58, math.pi, 2 * math.pi)
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(8)
        ctx.stroke()
        ctx.move_to(895, 1300)
        ctx.line_to(910, 1235)
        ctx.line_to(935, 1245)
        ctx.line_to(915, 1340)
        ctx.close_path()
        fill_stroke(ctx, hexc("ef5d6a"))
        rrect(ctx, 790, 1290, 130, 96, 26)
        fill_stroke(ctx, hexc("ef5d6a"))
        # a plate of cookies between the couple
        for dx in (-34, 0, 34):
            ellipse(ctx, 540 + dx, 1366, 26, 18)
            fill_stroke(ctx, hexc("c98a4b"), width=4)
        ellipse(ctx, 540, 1382, 76, 12)
        fill_stroke(ctx, hexc("fffaf0"), width=4)

    # ---------- rain ----------
    def _static_rain(self, ctx):
        ctx.set_source(vgrad(ctx, 500, 1500, "2f5f63", "5f9391"))
        ctx.paint()
        # buildings with warm windows
        for x, y, w, col in ((60, 640, 300, "24484d"), (360, 760, 330, "2d5458"), (690, 590, 340, "214146")):
            ctx.rectangle(x, y, w, 1560 - y)
            fill_stroke(ctx, hexc(col))
            for wy in range(y + 50, 1240, 130):
                for wx in range(x + 40, x + w - 70, 95):
                    rrect(ctx, wx, wy, 60, 84, 6)
                    lit = (wx * 7 + wy * 3) % 5 < 3
                    fill_stroke(ctx, hexc("ffd98a") if lit else hexc("3f6a6e"), width=4)
        # shop awning
        for i in range(7):
            ctx.move_to(170 + i * 60, 1310)
            ctx.line_to(230 + i * 60, 1310)
            ctx.line_to(240 + i * 66 - 12, 1400)
            ctx.line_to(170 + i * 66 - 12, 1400)
            ctx.close_path()
            fill_stroke(ctx, hexc("e2574c" if i % 2 else "fff0dc"), width=5)
        # wet pavement
        ctx.rectangle(0, 1560, W, H - 1560)
        ctx.set_source(vgrad(ctx, 1560, H, "4b6d70", "375256"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1560)
        ctx.line_to(W, 1560)
        ctx.stroke()
        for x, y, rx in ((190, 1720, 120), (860, 1750, 140), (540, 1830, 170)):
            ellipse(ctx, x, y, rx, rx * 0.2)
            ctx.set_source_rgba(*hexc("9fd0d0", 0.45))
            ctx.fill()

    def _live_rain(self, ctx, t, anim):
        # street lamp
        ctx.set_source_rgba(1, 0.86, 0.5, 0.2 + 0.03 * math.sin(t * 3))
        ellipse(ctx, 900, 1110, 150, 140)
        ctx.fill()
        rrect(ctx, 892, 1130, 16, 440, 6)
        fill_stroke(ctx, hexc("1c3236"), width=4)
        ellipse(ctx, 900, 1105, 40, 40)
        fill_stroke(ctx, hexc("ffe9a8"), width=5)
        # rain
        ctx.set_source_rgba(0.85, 0.96, 1, 0.5)
        ctx.set_line_width(4)
        for k in range(80):
            x = (k * 137.5) % (W + 100) - 50
            y = (t * (1050 + k % 5 * 130) + k * 211) % 1420 + 500
            ctx.move_to(x, y)
            ctx.line_to(x - 9, y + 46)
        ctx.stroke()
        # ripples in the puddles
        ctx.set_source_rgba(1, 1, 1, 0.55)
        ctx.set_line_width(3)
        for k, (x, y) in enumerate(((150, 1720), (230, 1730), (820, 1750), (900, 1745), (500, 1830), (600, 1825))):
            age = (t * 1.2 + k * 0.37) % 1
            ellipse(ctx, x, y, 4 + age * 36, 1 + age * 8)
            ctx.set_source_rgba(1, 1, 1, 0.6 * (1 - age))
            ctx.stroke()

    # ---------- snow ----------
    def _pine(self, ctx, x, y, s):
        rrect(ctx, x - 16 * s, y - 40 * s, 32 * s, 50 * s, 6)
        fill_stroke(ctx, hexc("7a5340"), width=5)
        for k, (top, half) in enumerate(((-300, 70), (-220, 100), (-130, 130))):
            ctx.move_to(x, y + top * s)
            ctx.line_to(x + half * s, y + (top + 130) * s)
            ctx.line_to(x - half * s, y + (top + 130) * s)
            ctx.close_path()
            fill_stroke(ctx, hexc("2f7f6b"), width=5)
            # snow on the branches
            ctx.move_to(x, y + top * s)
            ctx.line_to(x + half * 0.38 * s, y + (top + 50) * s)
            ctx.line_to(x - half * 0.38 * s, y + (top + 50) * s)
            ctx.close_path()
            ctx.set_source_rgba(1, 1, 1, 0.95)
            ctx.fill()

    def _static_snow(self, ctx):
        ctx.set_source(vgrad(ctx, 500, 1420, "b9c8f2", "edf1ff"))
        ctx.paint()
        for y0, col in ((1290, "dfe7fb"), (1400, "f2f5ff")):
            ctx.move_to(0, y0)
            ctx.curve_to(300, y0 - 110, 660, y0 + 60, W, y0 - 70)
            ctx.line_to(W, H)
            ctx.line_to(0, H)
            ctx.close_path()
            fill_stroke(ctx, hexc(col), width=5)
        # cabin with a lit window
        rrect(ctx, 430, 1090, 240, 190, 10)
        fill_stroke(ctx, hexc("a6623e"))
        ctx.move_to(400, 1100)
        ctx.line_to(550, 970)
        ctx.line_to(700, 1100)
        ctx.close_path()
        fill_stroke(ctx, hexc("fffdf8"))
        rrect(ctx, 505, 1140, 90, 80, 8)
        fill_stroke(ctx, hexc("ffd166"))
        for x in (165, 915):
            self._pine(ctx, x, 1440, 1.15)
        self._pine(ctx, 305, 1330, 0.7)
        # ground
        ctx.rectangle(0, 1590, W, H - 1590)
        ctx.set_source(vgrad(ctx, 1590, H, "ffffff", "d8e3f8"))
        ctx.fill()
        ctx.set_source_rgba(*hexc("9fb2dc"))
        ctx.set_line_width(5)
        ctx.move_to(0, 1590)
        ctx.curve_to(400, 1570, 700, 1605, W, 1585)
        ctx.stroke()

    def _live_snow(self, ctx, t, anim):
        # chimney smoke
        rrect(ctx, 610, 985, 36, 70, 4)
        fill_stroke(ctx, hexc("8c5236"), width=5)
        for k in range(4):
            rise = (t * 30 + k * 40) % 160
            ellipse(ctx, 628 + rise * 0.2 + math.sin(t + k + rise * 0.04) * 8, 975 - rise, 11 + rise * 0.1, 11 + rise * 0.1)
            ctx.set_source_rgba(1, 1, 1, 0.8 * (1 - rise / 160))
            ctx.fill()
        # snowflakes: dark enough rims to read against the pale sky
        for k in range(70):
            x = (k * 137.5 + math.sin(t * 0.8 + k) * 26) % W
            y = (t * (70 + k % 4 * 30) + k * 97) % 1440 + 500
            r = 5 + k % 3 * 3
            ellipse(ctx, x, y, r, r)
            ctx.set_source_rgba(*hexc("8ba0d6", 0.55))
            ctx.set_line_width(2)
            ctx.stroke_preserve()
            ctx.set_source_rgba(1, 1, 1, 0.98)
            ctx.fill()

    # ---------- autumn ----------
    def _static_autumn(self, ctx):
        ctx.set_source(vgrad(ctx, 500, 1420, "ff9e3d", "ffe0a0"))
        ctx.paint()
        ellipse(ctx, 700, 830, 120, 120)
        ctx.set_source_rgba(*hexc("fff3c4", 0.95))
        ctx.fill()
        for y0, col in ((1330, "d9662c"), (1440, "b94c22")):
            ctx.move_to(0, y0)
            ctx.curve_to(320, y0 - 110, 680, y0 + 50, W, y0 - 80)
            ctx.line_to(W, H)
            ctx.line_to(0, H)
            ctx.close_path()
            fill_stroke(ctx, hexc(col))
        # bench
        rrect(ctx, 400, 1430, 280, 22, 8)
        fill_stroke(ctx, hexc("6d3b1f"), width=5)
        rrect(ctx, 400, 1480, 280, 22, 8)
        fill_stroke(ctx, hexc("6d3b1f"), width=5)
        for x in (430, 630):
            rrect(ctx, x, 1430, 20, 150, 4)
            fill_stroke(ctx, hexc("4b2814"), width=5)
        # leafy ground
        ctx.rectangle(0, 1570, W, H - 1570)
        ctx.set_source(vgrad(ctx, 1570, H, "9c5526", "75401c"))
        ctx.fill()
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(6)
        ctx.move_to(0, 1570)
        ctx.line_to(W, 1570)
        ctx.stroke()
        for k in range(46):
            x = self.rng.uniform(0, W)
            y = self.rng.uniform(1590, 1880)
            self._leaf(ctx, x, y, 11, self.rng.uniform(0, 6), ("e8622c", "f2a33d", "c9391f")[k % 3])

    def _leaf(self, ctx, x, y, s, ang, col, width=3):
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(ang)
        ellipse(ctx, 0, 0, s, s * 0.55)
        ctx.restore()
        fill_stroke(ctx, hexc(col), width=width)

    def _live_autumn(self, ctx, t, anim):
        for x, col in ((160, "e8552a"), (925, "f29b2e")):
            rrect(ctx, x - 20, 1140, 40, 450, 14)
            fill_stroke(ctx, hexc("6d3b1f"))
            sway = math.sin(t * 1.1 + x) * 5
            for dx, dy, r in ((-70, 1060, 95), (70, 1060, 95), (0, 970, 125)):
                ellipse(ctx, x + dx + sway, dy, r, r)
                fill_stroke(ctx, hexc(col))
        for k in range(24):
            x = (k * 151 + math.sin(t * 0.9 + k) * 60 + t * 18) % W
            y = (t * (75 + k % 3 * 25) + k * 113) % 1160 + 540
            self._leaf(ctx, x, y, 15, t * 1.5 + k, ("e8622c", "c9391f", "f6b73c")[k % 3])
