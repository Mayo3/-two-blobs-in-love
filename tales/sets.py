"""The rooms the stories play in. Like the cast they are flat colour without outlines, as if cut
from paper: nothing here is shared with the backgrounds of Two Blobs in Love.

The stage shows about x 0-1080 and y 400-1920 when four people are on, and the middle 800 px
from y 700 down when two are; people stand on GROUND, so keep what matters behind and above them.
"""
import math
import random

import cairo

from shorts.cartoon.draw import ellipse, hexc, rrect
from shorts.cartoon.scenes import GROUND, H, W

WALL_END = GROUND - 70  # where the wall meets the floor
CREAM = "fbf5ea"
NAVY = "33415c"
WOOD = "8c5e3c"


def box(ctx, x, y, w, h, color, r=0, a=1.0):
    if r:
        rrect(ctx, x, y, w, h, r)
    else:
        ctx.rectangle(x, y, w, h)
    ctx.set_source_rgba(*hexc(color, a))
    ctx.fill()


def disc(ctx, x, y, rx, color, ry=None, a=1.0):
    ellipse(ctx, x, y, rx, ry or rx)
    ctx.set_source_rgba(*hexc(color, a))
    ctx.fill()


def poly(ctx, pts, color, a=1.0):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*hexc(color, a))
    ctx.fill()


def stroke(ctx, pts, width, color, a=1.0):
    ctx.set_source_rgba(*hexc(color, a))
    ctx.set_line_width(width)
    ctx.set_line_cap(1)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    ctx.set_line_cap(0)


def steam(ctx, x, y, t, color="ffffff"):
    """Three wisps rising from (x, y)."""
    for k in range(3):
        rise = (t * 26 + k * 21) % 64
        sx = x + (k - 1) * 16
        ctx.set_source_rgba(*hexc(color, 0.6 * (1 - rise / 64)))
        ctx.set_line_width(7)
        ctx.set_line_cap(1)
        ctx.move_to(sx, y - rise)
        ctx.curve_to(sx + 10, y - rise - 12, sx - 10, y - rise - 24, sx, y - rise - 36)
        ctx.stroke()
    ctx.set_line_cap(0)


def plant(ctx, x, base, pot="c8553d", size=1.0):
    for k, (ang, long) in enumerate(((-0.9, 150), (-0.45, 200), (0.0, 230), (0.4, 205), (0.85, 155), (-0.2, 150), (0.2, 140))):
        ctx.save()
        ctx.translate(x, base - 80 * size)
        ctx.rotate(ang)
        ellipse(ctx, 0, -long * size * 0.5, 30 * size, long * size * 0.5)
        ctx.set_source_rgba(*hexc("4f8a5b" if k % 2 else "5fa06b"))
        ctx.fill()
        ctx.restore()
    poly(ctx, [(x - 56 * size, base - 96 * size), (x + 56 * size, base - 96 * size), (x + 42 * size, base), (x - 42 * size, base)], pot)
    box(ctx, x - 62 * size, base - 104 * size, 124 * size, 22 * size, pot, 8)
    box(ctx, x - 62 * size, base - 86 * size, 124 * size, 6 * size, "000000", 0, 0.1)


def couch(ctx, x, base, wide, color, light):
    box(ctx, x + 30, base - 236, wide - 60, 190, color, 34)
    for ax in (x, x + wide - 76):
        box(ctx, ax, base - 170, 76, 156, color, 28)
    box(ctx, x + 56, base - 116, wide - 112, 74, light, 18)
    box(ctx, x + wide / 2 - 3, base - 116, 6, 74, color)
    box(ctx, x + 24, base - 60, wide - 48, 48, color, 10)
    for lx in (x + 44, x + wide - 60):
        box(ctx, lx, base - 14, 16, 26, WOOD, 4)


def window(ctx, x, y, wide, high, sky, frame=CREAM):
    box(ctx, x - 16, y - 16, wide + 32, high + 32, frame, 10)
    box(ctx, x, y, wide, high, sky)


def window_bars(ctx, x, y, wide, high, frame=CREAM):
    box(ctx, x + wide / 2 - 6, y, 12, high, frame)
    box(ctx, x, y + high * 0.45, wide, 12, frame)
    box(ctx, x - 30, y + high + 14, wide + 60, 20, frame, 6)


def moon(ctx, x, y, sky):
    disc(ctx, x, y, 38, "fdf0c2")
    disc(ctx, x - 16, y - 10, 34, sky)


class Room:
    """A place. Some come in versions, named after a dash: "home-empty" is the living room without its couch."""
    kinds = ("home", "home-empty", "home-chair", "home-bare", "nanas", "cafe", "kitchen", "office", "meeting", "street",
             "street-van", "hall", "bedroom", "den", "wedding", "beach")

    def __init__(self, kind):
        assert kind in self.kinds, kind
        self.kind, _, self.version = kind.partition("-")
        self.rng = random.Random(11)
        self.floor = hexc("000000")  # colour below the stage; each room sets its own
        self.static = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        getattr(self, f"_static_{self.kind}")(cairo.Context(self.static))

    def draw(self, ctx, t, stage=None):
        ctx.set_source_surface(self.static, 0, 0)
        ctx.paint()
        getattr(self, f"_live_{self.kind}")(ctx, t)

    def _planks(self, ctx, base, line):
        self.floor = hexc(base)
        box(ctx, 0, WALL_END, W, H - WALL_END, base)
        for row, y in enumerate(range(WALL_END, H, 66)):
            box(ctx, 0, y, W, 4, line)
            for x in range(-200 + (row * 270) % 400, W, 400):
                box(ctx, x, y, 4, 66, line)

    def _tiles(self, ctx, a, b, size=108):
        self.floor = hexc(a)
        box(ctx, 0, WALL_END, W, H - WALL_END, a)
        for row, y in enumerate(range(WALL_END, H, size)):
            for col, x in enumerate(range(0, W, size)):
                if (row + col) % 2:
                    box(ctx, x, y, size, size, b)

    # ---------- home: a living room by day ----------
    def _static_home(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "efe2d0")
        for x in range(0, W, 120):
            box(ctx, x, 0, 60, WALL_END, "ebdcc7")
        self._planks(ctx, "b98a62", "a87a54")
        box(ctx, 0, WALL_END - 26, W, 26, CREAM)
        if self.version != "bare":
            disc(ctx, 540, GROUND + 40, 450, "7a9e9f", 84)  # rug
            disc(ctx, 540, GROUND + 40, 390, "8fb0b0", 66)
        # window with a view, curtains
        wx, wy, ww, wh = 150, 800, 300, 400
        box(ctx, wx - 18, wy - 18, ww + 36, wh + 36, CREAM, 10)
        box(ctx, wx, wy, ww, wh, "bfe3ee")
        ctx.save()
        ctx.rectangle(wx, wy, ww, wh)
        ctx.clip()
        disc(ctx, wx + 222, wy + 104, 44, "ffe9a8")
        disc(ctx, wx + 50, wy + wh + 50, 230, "9fcf9a", 170)
        disc(ctx, wx + 290, wy + wh + 70, 220, "86bf86", 150)
        ctx.restore()
        self.window = (wx, wy, ww, wh)
        if self.version == "bare":  # everything has been carried out: the wall is paler where things stood
            for x, y, wide, high in ((250, 1370, 420, WALL_END - 1396), (820, 1140, 230, WALL_END - 1166), (610, 850, 150, 196), (800, 870, 200, 150)):
                box(ctx, x, y, wide, high, "f6eddf", 12)
            disc(ctx, 540, GROUND + 40, 450, "c79a72", 84)
            return
        # a lamp, pictures, a bookshelf, a plant
        box(ctx, 40, 1040, 12, WALL_END - 1040, NAVY)
        disc(ctx, 46, WALL_END - 4, 50, NAVY, 12)
        poly(ctx, [(4, 960), (88, 960), (112, 1064), (-20, 1064)], "f6d27a")
        box(ctx, 610, 850, 150, 196, CREAM, 6)
        box(ctx, 624, 864, 122, 168, "f4a261")
        disc(ctx, 685, 925, 34, "ffe9a8")
        poly(ctx, [(624, 1032), (624, 990), (670, 950), (706, 984), (728, 962), (746, 984), (746, 1032)], "e76f51")
        box(ctx, 800, 870, 200, 150, CREAM, 6)
        box(ctx, 814, 884, 172, 122, "577590")
        ctx.save()
        ctx.rectangle(814, 884, 172, 122)
        ctx.clip()
        disc(ctx, 950, 916, 20, CREAM)
        disc(ctx, 860, 1030, 110, "8fb0b0", 70)
        disc(ctx, 980, 1040, 90, "7a9e9f", 70)
        ctx.restore()
        box(ctx, 820, 1140, 230, WALL_END - 1140, WOOD, 8)
        for k in range(3):
            y0 = 1158 + k * 138
            box(ctx, 836, y0, 198, 120, "74492c")
            x = 842
            while x < 1000:
                wide, tall = self.rng.choice((18, 22, 26, 30)), self.rng.randint(74, 108)
                if self.rng.random() < 0.15:
                    x += 26
                    continue
                box(ctx, x, y0 + 120 - tall, wide, tall, self.rng.choice(("e76f51", "2a9d8f", "e9c46a", "577590", "e5989b", CREAM, "6d597a")), 3)
                x += wide + 3
        plant(ctx, 756, WALL_END - 6)
        if self.version == "":
            couch(ctx, 226, WALL_END + 16, 470, "6f9fd8", "9dc0ea")
        else:  # the couch is gone: the wall and the floor are paler where it stood
            box(ctx, 250, 1370, 420, WALL_END - 1396, "f6eddf", 24)
            poly(ctx, [(240, WALL_END), (680, WALL_END), (700, WALL_END + 44), (220, WALL_END + 44)], "c79a72")
        if self.version == "chair":  # the massage chair
            box(ctx, 392, 1290, 150, 290, "9d7bd8", 40)
            box(ctx, 410, 1310, 114, 150, "b79be6", 30)
            for ax in (364, 522):
                box(ctx, ax, 1420, 50, 176, "8a66c9", 22)
            box(ctx, 404, 1486, 126, 60, "b79be6", 16)
            box(ctx, 384, 1560, 166, 44, "8a66c9", 12)
            box(ctx, 532, 1436, 30, 44, CREAM, 8)
            disc(ctx, 547, 1450, 6, "e63946")

    def _live_home(self, ctx, t):
        if self.version == "chair":  # it hums
            for side in (-1, 1):
                for k in (0, 1):
                    dx = math.sin(t * 30 + k) * 3
                    stroke(ctx, [(467 + side * (118 + k * 20) + dx, 1330 + k * 14), (467 + side * (118 + k * 20) + dx, 1400 - k * 14)], 7, "e9c46a")
        wx, wy, ww, wh = self.window
        ctx.save()
        ctx.rectangle(wx, wy, ww, wh)
        ctx.clip()
        for k, (y, speed) in enumerate(((70, 9), (170, 6))):  # clouds drift past
            x = wx - 120 + (t * speed + k * 190) % (ww + 240)
            for dx, r in ((-34, 22), (0, 30), (36, 24)):
                disc(ctx, x + dx, wy + y, r, "ffffff", r * 0.8)
            box(ctx, x - 56, wy + y, 114, 22, "ffffff", 11)
        ctx.restore()
        box(ctx, wx + ww / 2 - 7, wy, 14, wh, CREAM)
        box(ctx, wx, wy + wh * 0.45, ww, 14, CREAM)
        box(ctx, wx - 40, wy + wh + 18, ww + 80, 22, CREAM, 6)
        for side in (-1, 1):  # curtains, stirring a little
            x0 = wx - 62 if side < 0 else wx + ww - 28
            sway = math.sin(t * 0.8 + side) * 5
            poly(ctx, [(x0, wy - 50), (x0 + 90, wy - 50), (x0 + 90 + sway + side * 10, wy + wh + 70), (x0 + sway - side * -10, wy + wh + 70)], "e0a93b")
            for k in (1, 2):
                stroke(ctx, [(x0 + k * 30, wy - 40), (x0 + k * 30 + sway * 0.7, wy + wh + 60)], 5, "c9942c")
        box(ctx, wx - 96, wy - 62, ww + 192, 14, WOOD, 7)
        if self.version == "bare":
            return
        glow = cairo.RadialGradient(46, 1064, 10, 46, 1064, 230)  # lamp light
        glow.add_color_stop_rgba(0, 1, 0.93, 0.66, 0.3 + 0.02 * math.sin(t * 3))
        glow.add_color_stop_rgba(1, 1, 0.93, 0.66, 0)
        ctx.set_source(glow)
        ctx.rectangle(0, 830, 290, 470)
        ctx.fill()

    # ---------- cafe ----------
    def _static_cafe(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "9cc9bd")
        box(ctx, 0, 1450, W, WALL_END - 1450, "e8d5b9")
        for x in range(30, W, 78):
            box(ctx, x, 1470, 5, WALL_END - 1470, "dcc6a6")
        box(ctx, 0, 1436, W, 18, WOOD)
        self._tiles(ctx, "e9dcc9", "d5c2a8")
        # the window onto the street, under a striped awning
        wx, wy, ww, wh = 70, 800, 420, 480
        box(ctx, wx - 16, wy - 16, ww + 32, wh + 32, NAVY, 10)
        box(ctx, wx, wy, ww, wh, "d7eef2")
        ctx.save()
        ctx.rectangle(wx, wy, ww, wh)
        ctx.clip()
        for x, wide, tall, col in ((wx - 10, 130, 300, "b7d3d6"), (wx + 130, 110, 380, "a9c9cd"), (wx + 250, 150, 260, "b7d3d6"), (wx + 370, 90, 340, "a9c9cd")):
            box(ctx, x, wy + wh - tall, wide, tall, col)
            for wy2 in range(int(wy + wh - tall + 24), wy + wh - 30, 56):
                for wx2 in range(int(x + 16), int(x + wide - 24), 38):
                    box(ctx, wx2, wy2, 18, 26, "d7eef2")
        for k in range(8):
            poly(ctx, [(wx + k * 56, wy), (wx + k * 56 + 56, wy), (wx + k * 56 + 56, wy + 70), (wx + k * 56 + 28, wy + 92), (wx + k * 56, wy + 70)],
                 "e76f51" if k % 2 else CREAM)
        ctx.restore()
        box(ctx, wx + ww / 2 - 6, wy + 92, 12, wh - 92, NAVY)
        # chalkboard menu
        box(ctx, 640, 800, 330, 300, WOOD, 10)
        box(ctx, 656, 816, 298, 268, NAVY, 4)
        stroke(ctx, [(720, 866), (890, 866)], 12, "ffffff", 0.9)
        for k, wide in enumerate((190, 150, 210, 130)):
            stroke(ctx, [(690, 920 + k * 40), (690 + wide, 920 + k * 40)], 7, "ffffff", 0.55)
            stroke(ctx, [(900, 920 + k * 40), (922, 920 + k * 40)], 7, "e9c46a", 0.9)
        # the counter with the coffee machine and a cake
        box(ctx, 600, 1300, W - 600, WALL_END - 1300, NAVY)
        box(ctx, 580, 1280, W - 580, 26, CREAM, 8)
        box(ctx, 660, 1140, 170, 140, "c8553d", 14)
        box(ctx, 676, 1160, 138, 44, "a8432f", 8)
        box(ctx, 712, 1204, 18, 34, "3d405b")
        box(ctx, 764, 1204, 18, 34, "3d405b")
        box(ctx, 696, 1240, 104, 40, "3d405b", 6)
        for k in range(3):
            box(ctx, 862, 1244 - k * 26, 60, 34, CREAM, 8)
        disc(ctx, 1000, 1276, 74, CREAM, 10)
        box(ctx, 950, 1218, 100, 52, "f4d3d7", 8)
        box(ctx, 950, 1218, 100, 16, "e5989b", 8)
        ellipse(ctx, 1000, 1270, 70, 96)
        ctx.save()
        ctx.rectangle(900, 1150, 200, 120)
        ctx.clip()
        ctx.set_source_rgba(1, 1, 1, 0.3)
        ctx.fill()
        ctx.restore()
        disc(ctx, 1000, 1170, 9, CREAM)
        plant(ctx, 548, WALL_END - 6, "e9c46a", 0.9)

    def _live_cafe(self, ctx, t):
        steam(ctx, 746, 1126, t)
        for k, x in enumerate((230, 540, 850)):  # lamps on long cords
            sway = math.sin(t * 1.1 + k * 1.7) * 0.025
            ctx.save()
            ctx.translate(x, 0)
            ctx.rotate(sway)
            box(ctx, -3, 0, 6, 640, "3d405b")
            poly(ctx, [(-26, 640), (26, 640), (74, 730), (-74, 730)], "e76f51")
            disc(ctx, 0, 732, 30, "ffe9a8", 18)
            ctx.restore()

    # ---------- kitchen: evening ----------
    def _static_kitchen(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "cfe3ea")
        self._tiles(ctx, "a9bcc4", "97adb7")
        box(ctx, 300, 1120, W - 300, 220, "f4f8f9")  # tiles behind the counter
        for x in range(300, W, 52):
            box(ctx, x, 1120, 4, 220, "dbe7ea")
        for y in range(1120, 1340, 52):
            box(ctx, 300, y, W - 300, 4, "dbe7ea")
        # window: it is dark out
        wx, wy, ww, wh = 350, 800, 250, 280
        box(ctx, wx - 16, wy - 16, ww + 32, wh + 32, CREAM, 10)
        box(ctx, wx, wy, ww, wh, "2b3a67")
        disc(ctx, wx + 176, wy + 84, 38, "fdf0c2")
        disc(ctx, wx + 160, wy + 74, 34, "2b3a67")
        for sx, sy in ((40, 50), (96, 130), (60, 210), (200, 190), (130, 36)):
            disc(ctx, wx + sx, wy + sy, 4, "ffffff")
        box(ctx, wx + ww / 2 - 6, wy, 12, wh, CREAM)
        box(ctx, wx - 30, wy + wh + 14, ww + 60, 20, CREAM, 6)
        disc(ctx, 670, 900, 56, CREAM)  # clock
        disc(ctx, 670, 900, 46, "ffffff")
        # cupboards on the wall
        box(ctx, 750, 800, 330, 270, CREAM, 8)
        box(ctx, 750, 1058, 330, 12, "e3dccd")
        for x in (750, 915):
            box(ctx, x + 158, 814, 4, 236, "e3dccd")
            disc(ctx, x + 134, 1010, 9, "5b7b8c")
        # counter
        box(ctx, 300, 1354, W - 300, WALL_END - 1354, "5b7b8c")
        for x in range(300, W, 195):
            box(ctx, x + 12, 1380, 171, WALL_END - 1400, "668899", 8)
            box(ctx, x + 70, 1396, 56, 10, CREAM, 5)
        box(ctx, 804, 1380, 171, WALL_END - 1400, "3d405b", 8)  # oven
        box(ctx, 822, 1420, 135, 110, "232838", 8)
        box(ctx, 824, 1392, 131, 10, CREAM, 5)
        box(ctx, 286, 1330, W - 286, 28, CREAM, 8)
        box(ctx, 826, 1262, 130, 68, "e76f51", 10)  # pot on the stove
        box(ctx, 808, 1282, 166, 12, "e76f51", 6)
        box(ctx, 818, 1250, 146, 16, "c8553d", 8)
        disc(ctx, 891, 1246, 12, "c8553d")
        disc(ctx, 440, 1282, 50, "e9c46a", 52)  # kettle
        box(ctx, 396, 1296, 88, 36, "e9c46a", 6)
        poly(ctx, [(480, 1270), (526, 1246), (530, 1260), (486, 1298)], "e9c46a")
        box(ctx, 424, 1222, 32, 14, NAVY, 7)
        poly(ctx, [(560, 1290), (700, 1290), (676, 1332), (584, 1332)], "577590")  # fruit bowl
        for fx, col in ((596, "e76f51"), (632, "f4a261"), (668, "e63946")):
            disc(ctx, fx, 1282, 22, col)
        box(ctx, 560, 1290, 140, 8, "577590")
        # fridge, with the router on top
        box(ctx, 40, 940, 230, WALL_END - 940, "eef3f4", 14)
        box(ctx, 40, 1178, 230, 6, "cfd9dc")
        box(ctx, 230, 1010, 14, 120, "9fb4bd", 7)
        box(ctx, 230, 1230, 14, 200, "9fb4bd", 7)
        box(ctx, 80, 1010, 70, 84, "ffe9a8")
        for k in range(3):
            box(ctx, 90, 1030 + k * 18, 50 - k * 10, 5, "c9b676")
        disc(ctx, 115, 1010, 8, "e63946")
        disc(ctx, 180, 1060, 12, "2a9d8f")
        box(ctx, 90, 904, 130, 36, NAVY, 8)
        for x in (104, 204):
            box(ctx, x, 850, 8, 60, NAVY, 4)

    def _live_kitchen(self, ctx, t):
        steam(ctx, 891, 1232, t)
        for k in range(3):  # the router's lights
            on = k == 0 or math.sin(t * (5 + k * 3) + k) > -0.2
            disc(ctx, 112 + k * 20, 922, 5, "8be28b" if on else "4a5a78")
        for ang, long, wide in ((t * 0.1, 26, 7), (t * 1.2, 36, 5)):  # clock hands
            stroke(ctx, [(670, 900), (670 + math.sin(ang) * long, 900 - math.cos(ang) * long)], wide, NAVY)
        disc(ctx, 670, 900, 6, NAVY)

    # ---------- nanas: grandmother's flat, where the couch came from ----------
    def _static_nanas(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "f1d9d6")
        for row, y in enumerate(range(420, WALL_END - 40, 88)):
            for x in range(40 + (row % 2) * 44, W, 88):
                disc(ctx, x, y, 10, "e5b9b9")
                disc(ctx, x, y, 4, CREAM)
        self._planks(ctx, "8e6a5b", "7f5c4e")
        box(ctx, 0, WALL_END - 26, W, 26, CREAM)
        disc(ctx, 540, GROUND + 40, 450, "b5838d", 84)
        disc(ctx, 540, GROUND + 40, 380, "c99aa2", 64)
        for x, y, r, col in ((250, 900, 62, "e9c46a"), (410, 980, 48, "8fb0b0"), (300, 1070, 40, "e76f51")):  # family photos
            disc(ctx, x, y, r + 12, WOOD, r * 1.25 + 12)
            disc(ctx, x, y, r, col, r * 1.25)
            disc(ctx, x, y - r * 0.2, r * 0.36, "d7a07a")
            disc(ctx, x, y + r * 0.75, r * 0.6, CREAM, r * 0.5)
        box(ctx, 800, 860, 150, WALL_END - 860, "74492c", 12)  # the tall clock
        disc(ctx, 875, 960, 56, CREAM)
        box(ctx, 824, 1060, 102, 400, "5f3b22", 8)
        couch(ctx, 226, WALL_END + 16, 470, "6f9fd8", "9dc0ea")
        box(ctx, 330, 1356, 110, 60, CREAM, 8)  # lace on the back
        box(ctx, 480, 1356, 110, 60, CREAM, 8)
        box(ctx, 60, 1420, 120, WALL_END - 1420, WOOD, 8)
        poly(ctx, [(70, 1300), (170, 1300), (196, 1400), (44, 1400)], "e5989b")
        box(ctx, 114, 1400, 12, 24, WOOD)

    def _live_nanas(self, ctx, t):
        swing = math.sin(t * 3.1) * 0.22
        ctx.save()
        ctx.translate(875, 1070)
        ctx.rotate(swing)
        box(ctx, -4, 0, 8, 230, "e9c46a")
        disc(ctx, 0, 240, 30, "e9c46a")
        ctx.restore()
        for ang, long, wide in ((t * 0.1 + 1, 28, 8), (t * 1.2, 40, 5)):
            stroke(ctx, [(875, 960), (875 + math.sin(ang) * long, 960 - math.cos(ang) * long)], wide, NAVY)

    # ---------- office ----------
    def _static_office(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "dfe6ee")
        self.floor = hexc("8d99ae")
        box(ctx, 0, WALL_END, W, H - WALL_END, "8d99ae")
        for x in range(0, W, 180):
            box(ctx, x, WALL_END, 5, H - WALL_END, "818da3")
        box(ctx, 0, WALL_END - 22, W, 22, "b9c4d2")
        window(ctx, 80, 780, 400, 360, "bfe3ee", "ffffff")  # the city, through blinds
        for x, tall, col in ((90, 220, "a9c9cd"), (190, 300, "9dbfc6"), (300, 180, "a9c9cd"), (390, 260, "9dbfc6")):
            box(ctx, x, 1140 - tall, 86, tall, col)
        for y in range(790, 1140, 36):
            box(ctx, 80, y, 400, 10, "ffffff", 0, 0.85)
        box(ctx, 600, 800, 400, 280, "ffffff", 10)  # whiteboard with a chart
        box(ctx, 600, 1068, 400, 14, "b9c4d2", 6)
        for k, tall in enumerate((70, 120, 90, 170)):
            box(ctx, 650 + k * 70, 1030 - tall, 44, tall, ("2a9d8f", "e9c46a", "e76f51", "577590")[k], 6)
        stroke(ctx, [(640, 900), (720, 870), (800, 890), (940, 830)], 7, "e63946")
        disc(ctx, 540, 860, 50, NAVY)  # clock
        disc(ctx, 540, 860, 40, "ffffff")
        # desks along the wall
        for x in (60, 600):
            box(ctx, x, 1400, 420, 24, "c9a27a", 8)
            box(ctx, x + 20, 1424, 16, WALL_END - 1424, "9aa5b5")
            box(ctx, x + 384, 1424, 16, WALL_END - 1424, "9aa5b5")
            box(ctx, x + 230, 1424, 150, 130, "b9c4d2", 6)
            box(ctx, x + 110, 1240, 200, 130, NAVY, 10)  # monitor
            box(ctx, x + 122, 1252, 176, 106, "8ecae6", 4)
            for k in range(3):
                box(ctx, x + 136, 1270 + k * 26, 110 - k * 26, 10, "ffffff", 5, 0.8)
            box(ctx, x + 200, 1370, 20, 30, NAVY)
            box(ctx, x + 160, 1392, 100, 10, NAVY, 5)
            box(ctx, x + 40, 1350, 44, 50, "e76f51", 8)  # mug
        for k in range(4):
            box(ctx, 648, 1360 - k * 14, 130, 12, ("ffffff", "ffe9a8", "ffffff", "e5989b")[k], 3)  # the paper pile
        box(ctx, 510, 1330, 70, WALL_END - 1330, "ffffff", 10)  # water cooler
        box(ctx, 516, 1220, 58, 116, "8ecae6", 16, 0.9)
        plant(ctx, 1020, WALL_END - 6, "577590", 0.8)

    def _live_office(self, ctx, t):
        for ang, long, wide in ((t * 0.1 + 2, 22, 7), (t * 1.2, 32, 5)):
            stroke(ctx, [(540, 860), (540 + math.sin(ang) * long, 860 - math.cos(ang) * long)], wide, NAVY)
        if int(t * 2) % 2:  # a cursor blinks
            box(ctx, 310, 1270, 8, 12, "ffffff")

    # ---------- street: the pavement, the road behind it, shops across ----------
    def _static_street(self, ctx):
        box(ctx, 0, 0, W, 1480, "bfe3ee")
        disc(ctx, 880, 620, 60, "ffe9a8")
        for x, wide, top, col in ((0, 300, 760, "d98f6a"), (300, 260, 900, "e9c46a"), (560, 300, 700, "8fb0b0"), (860, 220, 860, "e5989b")):
            box(ctx, x, top, wide, 1480 - top, col)
            box(ctx, x, top, wide, 22, "000000", 0, 0.1)
            for wy in range(top + 70, 1200, 130):
                for wx in range(x + 34, x + wide - 70, 96):
                    box(ctx, wx, wy, 56, 80, CREAM, 6)
                    box(ctx, wx + 6, wy + 6, 44, 68, "577590", 4)
        # the restaurant across the road
        box(ctx, 590, 1250, 240, 230, NAVY, 6)
        box(ctx, 604, 1264, 130, 160, "ffe9a8")
        box(ctx, 750, 1270, 66, 210, "c8553d", 6)
        disc(ctx, 764, 1380, 6, "ffe9a8")
        for k in range(6):
            poly(ctx, [(570 + k * 47, 1200), (617 + k * 47, 1200), (617 + k * 47, 1250), (593 + k * 47, 1268), (570 + k * 47, 1250)],
                 "e76f51" if k % 2 else CREAM)
        box(ctx, 60, 1300, 110, 180, "74492c", 6)  # a front door
        box(ctx, 330, 1290, 200, 190, "ffffff", 6)
        box(ctx, 342, 1302, 176, 130, "8ecae6")
        box(ctx, 0, 1480, W, WALL_END - 1480, "6b6f86")  # road
        for x in range(30, W, 200):
            box(ctx, x, 1528, 110, 12, "ffffff", 6, 0.8)
        self.floor = hexc("cfc8bd")
        box(ctx, 0, WALL_END, W, H - WALL_END, "cfc8bd")
        box(ctx, 0, WALL_END, W, 16, "b3ab9e")
        for x in range(-40, W, 216):
            box(ctx, x, WALL_END + 16, 5, H - WALL_END, "bdb5a8")
        box(ctx, 960, 1040, 14, WALL_END - 1040 + 30, "3d405b")  # street lamp
        box(ctx, 900, 1030, 74, 14, "3d405b", 7)
        poly(ctx, [(880, 1044), (930, 1044), (944, 1084), (866, 1084)], "ffe9a8")
        if self.version == "van":  # the buyer's van, the couch in the back
            couch(ctx, 96, 1500, 280, "6f9fd8", "9dc0ea")
            box(ctx, 60, 1330, 16, 190, "eef3f4")
            box(ctx, 60, 1316, 400, 20, "eef3f4", 8)
            box(ctx, 60, 1496, 470, 60, "eef3f4", 10)
            box(ctx, 380, 1330, 150, 190, "eef3f4", 20)
            box(ctx, 420, 1352, 96, 80, "8ecae6", 12)
            box(ctx, 60, 1540, 480, 16, "e76f51")
            for wx in (150, 440):
                disc(ctx, wx, 1560, 40, "2b2d42")
                disc(ctx, wx, 1560, 16, "b9c4d2")

    def _live_street(self, ctx, t):
        for k, (y, speed) in enumerate(((520, 10), (640, 7))):
            x = -160 + (t * speed + k * 520 + 200) % (W + 320)
            for dx, r in ((-50, 30), (0, 42), (52, 32)):
                disc(ctx, x + dx, y, r, "ffffff", r * 0.8)
            box(ctx, x - 80, y, 164, 30, "ffffff", 15)

    # ---------- hall: the stairwell of the building ----------
    def _static_hall(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "e6dccb")
        box(ctx, 0, 1300, W, WALL_END - 1300, "7d9d8c")
        box(ctx, 0, 1290, W, 14, "6b8a79")
        self._tiles(ctx, "d8cdbb", "b9ad9a")
        box(ctx, 0, WALL_END - 20, W, 20, "5f7d6c")
        for x, num, col in ((90, "3", "c8553d"), (420, "4", "577590")):  # two front doors
            box(ctx, x - 16, 936, 252, WALL_END - 936, CREAM, 8)
            box(ctx, x, 952, 220, WALL_END - 952, col, 4)
            box(ctx, x + 24, 980, 172, 220, "000000", 8, 0.1)
            box(ctx, x + 24, 1240, 172, 280, "000000", 8, 0.1)
            disc(ctx, x + 110, 1090, 20, "e9c46a")
            disc(ctx, x + 190, 1290, 12, "e9c46a")
            box(ctx, x + 10, WALL_END + 16, 200, 34, "8c5e3c", 8)
        poly(ctx, [(720, WALL_END)] + [pt for k in range(7) for pt in ((720 + k * 60, WALL_END - k * 70 - 70), (780 + k * 60, WALL_END - k * 70 - 70))]
             + [(1140, WALL_END)], "b9ad9a")  # stairs going up
        for k in range(7):
            box(ctx, 720 + k * 60, WALL_END - k * 70 - 70, 60 + 400, 14, "d8cdbb")
        stroke(ctx, [(700, WALL_END - 250), (1120, WALL_END - 740)], 18, WOOD)
        for k in range(7):
            box(ctx, 716 + k * 60, WALL_END - 232 - k * 70, 8, 240, WOOD)
        for k in range(4):  # letter boxes
            box(ctx, 730 + k * 78, 880, 66, 90, "9fb4bd", 6)
            box(ctx, 742 + k * 78, 900, 42, 8, NAVY, 4)
        box(ctx, 334, 400, 6, 330, "3d405b")
        disc(ctx, 337, 760, 44, "ffe9a8", 40)

    def _live_hall(self, ctx, t):
        glow = cairo.RadialGradient(337, 760, 20, 337, 760, 260)
        glow.add_color_stop_rgba(0, 1, 0.93, 0.66, 0.28 + 0.03 * math.sin(t * 7))
        glow.add_color_stop_rgba(1, 1, 0.93, 0.66, 0)
        ctx.set_source(glow)
        ctx.rectangle(60, 500, 560, 520)
        ctx.fill()

    # ---------- bedroom, at night ----------
    def _static_bedroom(self, ctx):
        sky = "1f2a4d"
        box(ctx, 0, 0, W, WALL_END, "6072a3")
        self._planks(ctx, "6d597a", "5f4d6b")
        box(ctx, 0, WALL_END - 24, W, 24, "8090bd")
        window(ctx, 130, 800, 280, 340, sky)
        moon(ctx, 320, 890, sky)
        for sx, sy in ((170, 850), (230, 960), (190, 1060), (350, 1040), (270, 830)):
            disc(ctx, sx, sy, 4, "ffffff")
        window_bars(ctx, 130, 800, 280, 340)
        for x0 in (70, 380):
            poly(ctx, [(x0, 760), (x0 + 84, 760), (x0 + 90, 1200), (x0 - 6, 1200)], "3d4a7a")
        box(ctx, 50, 746, 440, 14, WOOD, 7)
        box(ctx, 520, 1180, 500, 300, "8c5e3c", 30)  # the bed
        box(ctx, 500, 1400, 540, WALL_END - 1390, "e5989b", 24)
        box(ctx, 500, 1400, 540, 60, CREAM, 24)
        box(ctx, 560, 1310, 180, 100, "ffffff", 30)
        box(ctx, 790, 1310, 180, 100, "ffffff", 30)
        box(ctx, 380, 1440, 110, WALL_END - 1440, WOOD, 8)  # bedside table and lamp
        disc(ctx, 435, 1500, 8, "e9c46a")
        box(ctx, 429, 1390, 12, 50, NAVY)
        poly(ctx, [(400, 1320), (470, 1320), (490, 1392), (380, 1392)], "f6d27a")
        box(ctx, 640, 880, 250, 180, CREAM, 6)  # a poster
        box(ctx, 654, 894, 222, 152, "2a9d8f")
        disc(ctx, 765, 970, 44, "e9c46a")

    def _live_bedroom(self, ctx, t):
        for sx, sy in ((230, 960), (350, 1040)):
            disc(ctx, sx, sy, 4 + 2 * math.sin(t * 2 + sx), "ffffff")
        glow = cairo.RadialGradient(435, 1380, 10, 435, 1380, 300)
        glow.add_color_stop_rgba(0, 1, 0.93, 0.66, 0.36 + 0.02 * math.sin(t * 3))
        glow.add_color_stop_rgba(1, 1, 0.93, 0.66, 0)
        ctx.set_source(glow)
        ctx.rectangle(130, 1080, 610, 510)
        ctx.fill()

    # ---------- den: the landlord's flat and his television ----------
    def _static_den(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "d9c08f")
        for x in range(0, W, 90):
            box(ctx, x, 0, 8, WALL_END, "cdb27f")
        self._planks(ctx, "7f5539", "6f4930")
        box(ctx, 0, WALL_END - 26, W, 26, "5f3b22")
        box(ctx, 120, 1420, 520, WALL_END - 1410, "5f3b22", 10)  # the television on its cupboard
        for x in (150, 400):
            box(ctx, x, 1446, 210, 110, "74492c", 8)
            disc(ctx, x + 105, 1500, 8, "e9c46a")
        box(ctx, 150, 1070, 460, 300, "2b2d42", 16)
        box(ctx, 360, 1370, 40, 40, "2b2d42")
        box(ctx, 290, 1400, 180, 20, "2b2d42", 8)
        box(ctx, 700, 1330, 300, WALL_END - 1316, "6a994e", 40)  # his armchair
        for k in range(4):
            box(ctx, 700 + k * 80, 1330, 12, WALL_END - 1330, "5c8743")
        for ax in (670, 960):
            box(ctx, ax, 1440, 70, WALL_END - 1424, "5c8743", 26)
        box(ctx, 700, 840, 280, 190, WOOD, 8)  # a photo of the building, framed
        box(ctx, 716, 856, 248, 158, "bfe3ee")
        box(ctx, 790, 880, 100, 134, "d98f6a")
        for wy in (896, 940, 984):
            for wx in (806, 850):
                box(ctx, wx, wy, 24, 26, CREAM)
        box(ctx, 240, 860, 250, 70, WOOD, 10)  # the prize fish
        disc(ctx, 360, 880, 86, "8fb0b0", 30)
        poly(ctx, [(430, 880), (480, 850), (480, 910)], "8fb0b0")
        disc(ctx, 310, 874, 6, "2b2d42")

    def _live_den(self, ctx, t):
        box(ctx, 166, 1086, 428, 268, "3d4f8f", 6)  # the show, frozen
        disc(ctx, 300, 1250, 70, "577590", 80)
        disc(ctx, 300, 1170, 40, "d7a07a")
        disc(ctx, 470, 1260, 60, "c8553d", 70)
        disc(ctx, 470, 1190, 36, "f0c4a0")
        box(ctx, 166, 1086, 428, 268, "2b2d42", 6, 0.35)
        for k in range(8):
            a = k * math.pi / 4
            lit = (int(t * 8) - k) % 8
            disc(ctx, 380 + math.cos(a) * 44, 1220 + math.sin(a) * 44, 12, "ffffff", None, 1 - lit * 0.11)

    # ---------- meeting: the room where the big client sits ----------
    def _static_meeting(self, ctx):
        box(ctx, 0, 0, W, WALL_END, "d5dbe4")
        self.floor = hexc("7c879c")
        box(ctx, 0, WALL_END, W, H - WALL_END, "7c879c")
        for x in range(0, W, 180):
            box(ctx, x, WALL_END, 5, H - WALL_END, "707b90")
        box(ctx, 0, WALL_END - 22, W, 22, "b9c4d2")
        for x in (0, 930):  # tall windows on the city
            box(ctx, x, 560, 150, 860, "bfe3ee")
            for bx, tall, col in ((x + 10, 420, "a9c9cd"), (x + 70, 560, "9dbfc6")):
                box(ctx, bx, 1420 - tall, 64, tall, col)
            box(ctx, x, 560, 150, 14, "ffffff")
            box(ctx, x + (140 if x == 0 else 0), 560, 10, 860, "ffffff")
        box(ctx, 220, 700, 640, 420, NAVY, 14)  # the screen
        box(ctx, 236, 716, 608, 388, "1f2638", 6)
        box(ctx, 276, 756, 300, 22, "ffffff", 8)
        box(ctx, 276, 796, 190, 12, "8ecae6", 6)
        for k, tall in enumerate((60, 96, 84, 150, 210)):
            box(ctx, 300 + k * 100, 1070 - tall, 62, tall, ("577590", "577590", "577590", "2a9d8f", "e9c46a")[k], 6)
        stroke(ctx, [(330, 1000), (430, 960), (530, 972), (630, 900), (740, 820)], 7, "e76f51")
        box(ctx, 520, 1120, 40, 60, NAVY)
        box(ctx, 60, 1420, 960, 30, "c9a27a", 10)  # the long table
        box(ctx, 90, 1450, 900, WALL_END - 1450, "9a7a58")
        for x in (150, 380, 610, 840):
            box(ctx, x, 1320, 100, 110, "3d405b", 20)
        for x in (250, 700):
            box(ctx, x, 1392, 90, 28, "eef3f4", 4)
        box(ctx, 470, 1380, 44, 40, "e76f51", 8)

    def _live_meeting(self, ctx, t):
        if int(t * 1.5) % 2:
            disc(ctx, 812, 746, 7, "e63946")

    # ---------- wedding: a garden, the arch, the guests' chairs ----------
    def _static_wedding(self, ctx):
        box(ctx, 0, 0, W, 1300, "cfe6ee")
        disc(ctx, 860, 640, 70, "fff3c9")
        for x, r in ((80, 230), (330, 280), (620, 250), (900, 290), (1060, 220)):  # trees
            disc(ctx, x, 1180, r, "86b383", r * 0.9)
        box(ctx, 0, 1220, W, WALL_END - 1220, "6f9a6a")
        for x in range(-20, W, 96):
            disc(ctx, x + 48, 1224, 60, "6f9a6a", 34)
        self.floor = hexc("9cc08a")
        box(ctx, 0, WALL_END, W, H - WALL_END, "9cc08a")
        poly(ctx, [(400, WALL_END), (680, WALL_END), (800, H), (280, H)], "f4ece2")  # the aisle
        for side in (-1, 1):  # rows of white chairs
            for row in range(3):
                for k in range(3):
                    x = 540 + side * (250 + k * 96 + row * 22)
                    y = 1470 + row * 46
                    box(ctx, x - 34, y, 68, 84, "ffffff", 10)
                    box(ctx, x - 34, y + 70, 68, 60, "f1ece4", 6)
        for x in (372, 692):  # the arch
            box(ctx, x, 800, 16, WALL_END - 790, "f4ece2")
        ctx.set_source_rgba(*hexc("f4ece2"))
        ctx.set_line_width(16)
        ctx.new_sub_path()
        ctx.arc(540, 820, 160, math.pi, 2 * math.pi)
        ctx.stroke()
        for k in range(26):  # flowers over it and down one side
            a = math.pi + k / 25 * math.pi
            x, y = 540 + math.cos(a) * 160, 820 + math.sin(a) * 160
            disc(ctx, x + self.rng.uniform(-14, 14), y + self.rng.uniform(-14, 14), self.rng.uniform(20, 34),
                 self.rng.choice(("ffffff", "f3c9cf", "e5989b", "8fb58a", "f6e1b5")))
        for k in range(12):
            disc(ctx, 380 + self.rng.uniform(-22, 22), 830 + k * 44, self.rng.uniform(18, 30), self.rng.choice(("ffffff", "f3c9cf", "8fb58a")))

    def _live_wedding(self, ctx, t):
        for k in range(14):  # a string of lights
            x = 40 + k * 77
            y = 520 + 60 * math.sin(k / 13 * math.pi)
            disc(ctx, x, y, 9 + 2 * math.sin(t * 3 + k * 1.7), "fff3c9")
        for k in range(8):  # petals on the air
            x = (k * 151 + t * 20) % W
            y = 700 + (k * 97 + t * (26 + k * 3)) % 860
            disc(ctx, x, y, 7, "f3c9cf", 4)

    # ---------- beach: the honeymoon ----------
    def _static_beach(self, ctx):
        g = cairo.LinearGradient(0, 300, 0, 1320)
        g.add_color_stop_rgba(0, *hexc("f2a98a"))
        g.add_color_stop_rgba(1, *hexc("fbe3c0"))
        ctx.set_source(g)
        ctx.rectangle(0, 0, W, 1320)
        ctx.fill()
        disc(ctx, 700, 1300, 110, "fff3c9")
        box(ctx, 0, 1320, W, WALL_END - 1320, "4f9aa8")
        box(ctx, 600, 1330, 200, 10, "fff3c9", 5, 0.7)
        box(ctx, 640, 1360, 120, 8, "fff3c9", 4, 0.5)
        self.floor = hexc("ead7b0")
        box(ctx, 0, WALL_END - 30, W, H, "ead7b0")
        disc(ctx, 300, WALL_END - 20, 500, "ead7b0", 60)
        stroke(ctx, [(120, WALL_END), (150, 1300), (200, 1020)], 30, "8c5e3c")  # a palm
        for ang in (-2.6, -2.0, -1.3, -0.6, 0.0, 0.5):
            ctx.save()
            ctx.translate(200, 1020)
            ctx.rotate(ang)
            ellipse(ctx, 130, 0, 150, 34)
            ctx.set_source_rgba(*hexc("4f8a5b"))
            ctx.fill()
            ctx.restore()
        box(ctx, 846, 1180, 12, WALL_END - 1180, "f4ece2")  # a parasol and a sunbed
        ctx.new_sub_path()
        ctx.arc(852, 1200, 190, math.pi, 2 * math.pi)
        ctx.close_path()
        ctx.set_source_rgba(*hexc("e76f51"))
        ctx.fill()
        for k in (-1, 1):
            ctx.new_sub_path()
            ctx.move_to(852, 1200)
            ctx.arc(852, 1200, 190, math.pi * (1.5 + k * 0.33) - 0.26, math.pi * (1.5 + k * 0.33) + 0.26)
            ctx.close_path()
            ctx.set_source_rgba(*hexc("f4ece2"))
            ctx.fill()
        poly(ctx, [(700, WALL_END - 40), (980, WALL_END - 40), (1010, WALL_END - 130), (990, WALL_END - 136), (960, WALL_END - 64), (700, WALL_END - 64)], "f4ece2")
        box(ctx, 720, WALL_END - 40, 12, 40, "8c5e3c")
        box(ctx, 950, WALL_END - 40, 12, 40, "8c5e3c")

    def _live_beach(self, ctx, t):
        for k in range(4):
            x = (k * 300 + t * 24) % (W + 200) - 100
            y = 1390 + k * 44
            box(ctx, x, y + 3 * math.sin(t * 2 + k), 150, 8, "ffffff", 4, 0.55)
