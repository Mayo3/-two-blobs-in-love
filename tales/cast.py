"""The cast: a small troupe of adults who play a different part in every story (the fiancé, the best
friend, the boss), each with their own build, face, hair, clothes, resting expression and voice.

The look is deliberately not that of Two Blobs in Love, and it is drawn for viewers in their twenties:
adult proportions, faces with a character of their own (a raised brow, a smirk, heavy lids), styled
hair, clothes somebody would wear. Nothing has an ink outline: every part is rounded with soft light
and shadow, like the figures of a life-simulation game. Arms bend at the elbow, so people cross them, put a hand on a hip or hold a glass
instead of standing with their arms out.
Only the easing of poses, the blinking and the darting eyes are borrowed from the blobs' code.
"""
import math
import os

import cairo

from shorts import tts
from shorts.cartoon.characters import BLINK, Blob
from shorts.cartoon.draw import ellipse, hexc, rrect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_DIR = os.path.join(ROOT, "voices", "tales")
INK_HEX = "2b2d42"  # eyes, text
INK = hexc(INK_HEX)
MOUTH = hexc("7a2a36")
GOLD = hexc("e2b84d")

# A body at height 1.0, in stage pixels: feet to hip, hip to shoulder, neck, and the unit the head is drawn in.
LEG, TORSO, NECK, U = 285, 178, 20, 47
HEAD = LEG + TORSO + NECK + 49  # feet to the middle of the face
UPPER_ARM, FOREARM = 100, 92
REST_ARM = (6.0, -5.0)  # an arm hanging loose: the upper arm's and the forearm's angle (see Actor.reset)

# tall: height; sw / ww / hw: shoulders, waist, hips. color is the top they wear; tag: the colour of their name tag;
# caption: a light tint for the word being spoken. rest: the face they make when nothing is going on.
# kokoro: the synthetic voice their Chatterbox voice is copied from, and their backup voice.
CAST = {
    "mara": dict(label="Mara", color="2f7f79", tag="2f7f79", caption="9BE7DC", tall=0.95, sw=116, ww=80, hw=106, skin="d9a47e",
                 hair="2e1f1b", eye="6b4426", look="pony", outfit="blazer", under="f1ece4", bottom="2b3147", shoes="ece7df", woman=True,
                 necklace=True, mole=True, rest=dict(mouth="flat", cock=0.7, lid=0.25),
                 kokoro="af_bella", about="Calm on the outside. Keeps every receipt and every screenshot."),
    "dex": dict(label="Dex", color="5b6b4f", tag="5b6b4f", caption="D5E8B8", tall=1.0, sw=150, ww=112, hw=110, skin="c98f68",
                hair="241713", eye="5a3d2b", look="quiff", outfit="bomber", under="f1ece4", bottom="3b3f4a", shoes="ece7df", stubble=True,
                chain=True, rest=dict(mouth="smirk", cock=0.3, lid=0.2),
                kokoro="am_michael", about="Charming, quick with an excuse, sure he will never get caught."),
    "lulu": dict(label="Lulu", color="d99a2b", tag="c98a1b", caption="FFEB9C", tall=0.93, sw=114, ww=78, hw=110, skin="8a573a",
                 hair="1f1614", eye="4a2c1a", look="curls", outfit="blouse", under="d99a2b", bottom="3a3550", shoes="c8553d", woman=True,
                 hoops=True, band="c8553d", rest=dict(mouth="smile", cock=0.0, lid=0.0),
                 kokoro="af_aoede", about="Loud, loyal, the first to arrive and the last to leave. Usually."),
    "theo": dict(label="Theo", color="4f6b8a", tag="4f6b8a", caption="B9D6FF", tall=1.04, sw=138, ww=104, hw=104, skin="f0cba6",
                 hair="1c1c26", eye="3f5f8a", look="curtain", outfit="turtleneck", under="4f6b8a", bottom="33364a", shoes="ece7df",
                 glasses=True, freckles=True, rest=dict(mouth="flat", cock=0.0, lid=0.0, brow=-0.35),
                 kokoro="am_fenrir", about="Quiet, careful, does the work other people take the credit for."),
    "ivy": dict(label="Ivy", color="2b2d42", tag="8c3b4a", caption="FFC2CC", tall=0.97, sw=114, ww=76, hw=104, skin="f3d3b8",
                hair="efe0bd", eye="5f8f7a", look="bob", outfit="leather", under="8c3b4a", bottom="8c3b4a", shoes="2b2d42", woman=True,
                skirt=True, choker=True, lips="b0303e", rest=dict(mouth="smirk", cock=0.0, lid=0.45),
                kokoro="af_nova", about="Always smiling, always borrowing, never quite telling the whole story."),
    "gus": dict(label="Gus", color="5a5f6e", tag="5a5f6e", caption="D3D8E8", tall=0.98, sw=170, ww=156, hw=152, skin="eec3a0",
                hair="8f8a86", eye="5c4a3d", look="bald", outfit="cardigan", under="e9e2d0", bottom="4a3f38", shoes="2e2422", beard=True,
                rest=dict(mouth="flat", cock=0.0, lid=0.3, brow=0.45),
                kokoro="bm_george", about="The older man in the story: the boss, the landlord, somebody's father."),
}
SPEAKER_COLORS = {k: v["caption"] for k, v in CAST.items()}

# the voice code looks characters up in one table; ours join Pip and Bo there
for _name, _spec in CAST.items():
    tts.CAST[_name] = {"ref": os.path.join(VOICE_DIR, f"{_name}.wav"), "backup": _spec["kokoro"]}


def shade(c, k=0.2):
    return (c[0] * (1 - k), c[1] * (1 - k), c[2] * (1 - k), c[3])


def tint(c, k=0.3):
    return (c[0] + (1 - c[0]) * k, c[1] + (1 - c[1]) * k, c[2] + (1 - c[2]) * k, c[3])


def lit(ctx, fill):
    """A gradient across the current path, lighter toward the upper left: what makes a flat shape look round."""
    x1, y1, x2, y2 = ctx.path_extents()
    g = cairo.LinearGradient(x1, y1, x2, y1 + (y2 - y1) * 0.3)
    g.add_color_stop_rgba(0, *tint(fill, 0.17))
    g.add_color_stop_rgba(0.45, *fill)
    g.add_color_stop_rgba(1, *shade(fill, 0.26))
    return g


def paint(ctx, fill, edge=3.0):
    """Fill the current path as a rounded form. `edge` only asks for the faint darker rim that keeps two
    parts of the same colour apart; nothing is outlined in ink."""
    ctx.set_source(lit(ctx, fill))
    if edge:
        ctx.fill_preserve()
        ctx.set_source_rgba(*shade(fill, 0.42)[:3], 0.5)
        ctx.set_line_width(1.6)
        ctx.set_line_join(1)
        ctx.stroke()
    else:
        ctx.fill()


class Actor(Blob):
    def __init__(self, key, x, ground, seed=0):
        self.key = key
        self.spec = s = CAST[key]
        self.rest = s["rest"]
        super().__init__(s["label"], s["color"], None, x, ground, 1.0, 1, seed)
        self.k = s["tall"]
        self.skin, self.hair, self.top_color = hexc(s["skin"]), hexc(s["hair"]), hexc(s["color"])
        self.under, self.bottom, self.shoes, self.iris = hexc(s["under"]), hexc(s["bottom"]), hexc(s["shoes"]), hexc(s["eye"])
        self.sw, self.ww, self.hw = s["sw"], s["ww"], s["hw"]
        self.tag_color = hexc(s["tag"])  # behind their name in white
        self.line = shade(self.hair, 0.3) if self.hair[0] < 0.6 else hexc("6a5f58")  # lashes and brows
        self.weight = 1 if seed % 2 else -1  # the leg they stand on

    def reset(self, home_x):
        """Default targets at the start of every frame; feelings override them.
        ua_* / fa_*: the upper arm's and the forearm's angle in degrees from hanging straight down, for the
        arm toward the other person (in) and the one away (out); positive swings out from the body, negative
        across it. brow: +1 angry, -1 worried. raise: brows lifted. cock: one brow up. lid: 0 open, 1 heavy."""
        super().reset(home_x)
        r = self.rest
        for key, v in (("brow", r.get("brow", 0.0)), ("raise", 0.0), ("cock", r.get("cock", 0.0)), ("lid", r.get("lid", 0.0)),
                       ("ua_in", REST_ARM[0]), ("fa_in", REST_ARM[1]), ("ua_out", REST_ARM[0]), ("fa_out", REST_ARM[1]),
                       ("tip", 0.0)):
            self.cur.setdefault(key, v)
            self.tgt[key] = v
        self.tgt["blush"] = 0.0
        self.tgt["look_x"] = 0.4 * self.inner
        self.mouth = r.get("mouth", "flat")
        self.tears = False
        self.fuming = False
        self.pocket = set()  # "in" / "out": that hand is in a pocket

    def dims(self):
        """Half width and half height, for framing."""
        return (self.sw / 2 + 24) * self.k, (HEAD + 60) * self.k / 2

    def top(self):
        """Stage y of the top of the head, hair included."""
        return self.ground - (HEAD + 1.4 * U + {"curls": 46, "quiff": 20}.get(self.spec["look"], 6)) * self.k

    def head_y(self):
        """Stage y of the middle of the face."""
        return self.ground - HEAD * self.k

    def _shoulder(self, side):
        return side * (self.sw / 2 - 13), -(LEG + TORSO) + 20

    def _arm_angles(self, side):
        w = "in" if side == self.inner else "out"
        return math.radians(self.cur[f"ua_{w}"]), math.radians(self.cur[f"fa_{w}"])

    def hand_pos(self, side):
        px, py = self._shoulder(side)
        up, fore = self._arm_angles(side)
        x = px + side * (math.sin(up) * UPPER_ARM + math.sin(fore) * FOREARM)
        y = py + math.cos(up) * UPPER_ARM + math.cos(fore) * FOREARM
        return self.cur["x"] + x * self.k, self.ground + y * self.k

    def draw(self, ctx, t):
        c = self.cur
        if c["alpha"] < 0.02:
            return
        self.now = t
        k = self.k
        breath = math.sin(t * self.breath_rate + self.breath_phase)
        squash = c["squash"] * 0.25
        hop = abs(math.sin(t * 9)) * 9 * self.hop
        x = c["x"] + math.sin(t * 60) * 2.5 * c["shiver"]
        ctx.save()  # a soft shadow on the floor
        ctx.translate(c["x"], self.ground + 4)
        ctx.scale(1, 0.16)
        g = cairo.RadialGradient(0, 0, 10, 0, 0, self.hw * 1.1 * k)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.42)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g)
        ctx.arc(0, 0, self.hw * 1.1 * k, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

        ctx.save()
        ctx.translate(x, self.ground - hop)
        ctx.scale(k * (1 + squash), k * (1 - squash))
        self._legs(ctx, t)
        ctx.translate(self.weight * 5, -LEG)  # the weight is on one leg; everything above the hips leans and breathes
        ctx.rotate(math.radians(c["lean"] * 0.7 - self.weight * 1.4 + 0.4 * math.sin(t * self.breath_rate * 0.31 + self.breath_phase * 2)))
        ctx.translate(0, LEG - breath * 1.5)
        tilt = math.radians(c["lean"] * 0.3 + c["look_x"] * 3 + c["tip"] + self.weight * 2.2)
        ctx.save()
        ctx.translate(0, -HEAD)
        ctx.rotate(tilt)
        self._hair_back(ctx)
        ctx.restore()
        rrect(ctx, -14, -(LEG + TORSO) - NECK - 14, 28, NECK + 28, 8)  # neck
        paint(ctx, shade(self.skin, 0.12))
        if self.spec.get("choker"):
            ctx.rectangle(-14, -(LEG + TORSO) - NECK + 2, 28, 7)
            ctx.set_source_rgba(*INK)
            ctx.fill()
        self._torso(ctx)
        self._arm(ctx, -self.inner)
        self._arm(ctx, self.inner)
        ctx.translate(0, -HEAD)
        ctx.rotate(tilt)
        self._head(ctx, t, c)
        ctx.restore()

        hx, hy = x, self.ground - hop - HEAD * k
        if self.sweat:
            sx, sy = hx - self.inner * U * 0.95 * k, hy - 30 + (t * 34 % 26)
            ctx.move_to(sx, sy - 13)
            ctx.curve_to(sx + 9, sy, sx + 7, sy + 10, sx, sy + 10)
            ctx.curve_to(sx - 7, sy + 10, sx - 9, sy, sx, sy - 13)
            paint(ctx, hexc("9fd3ea"), 2)

    # ---------- body ----------

    def _legs(self, ctx, t):
        s = self.spec
        step = math.sin(t * 9) * self.hop
        skirt = s.get("skirt")
        wide_leg = s["outfit"] == "blouse"
        for side in (-1, 1):
            lift = max(0.0, side * step) * 14
            free = side != self.weight  # the leg without the weight stands a little out, its foot turned
            top_x, foot_x = side * self.hw * 0.25, side * (self.hw * 0.2 + (16 if free else 2))
            thigh, ankle = self.hw * 0.5, 26 if skirt else 54 if wide_leg else 36
            ctx.move_to(top_x - thigh / 2, -LEG - 8)
            ctx.line_to(top_x + thigh / 2, -LEG - 8)
            ctx.curve_to(top_x + thigh / 2, -LEG * 0.5, foot_x + ankle / 2 + side * 4, -LEG * 0.45, foot_x + ankle / 2, -20 - lift)
            ctx.line_to(foot_x - ankle / 2, -20 - lift)
            ctx.curve_to(foot_x - ankle / 2 + side * 4, -LEG * 0.45, top_x - thigh / 2, -LEG * 0.5, top_x - thigh / 2, -LEG - 8)
            ctx.close_path()
            paint(ctx, self.skin if skirt else self.bottom)
            sx = foot_x - 27 + side * (12 if free else 6)
            rrect(ctx, sx, -24 - lift, 56, 24, 11)
            paint(ctx, self.shoes)
            rrect(ctx, sx, -7 - lift, 56, 7, 3)
            paint(ctx, shade(self.shoes, 0.35), 0)
        if skirt:  # to above the knee
            ctx.move_to(-self.hw / 2, -LEG - 20)
            ctx.line_to(self.hw / 2, -LEG - 20)
            ctx.line_to(self.hw * 0.56, -LEG + 104)
            ctx.line_to(-self.hw * 0.56, -LEG + 104)
            ctx.close_path()
            paint(ctx, self.bottom)
        else:
            rrect(ctx, -self.hw / 2, -LEG - 26, self.hw, 44, 14)
            paint(ctx, self.bottom)

    def _torso(self, ctx):
        sw, ww, hw, s = self.sw, self.ww, self.hw, self.spec
        sy, hy = -(LEG + TORSO), -LEG - 4
        wy = sy + TORSO * 0.62
        ctx.new_path()
        ctx.move_to(-sw / 2, sy + 34)
        ctx.curve_to(-sw / 2, sy + 10, -sw / 2 + 16, sy + 2, -20, sy - 8)
        ctx.line_to(20, sy - 8)
        ctx.curve_to(sw / 2 - 16, sy + 2, sw / 2, sy + 10, sw / 2, sy + 34)
        ctx.curve_to(sw / 2 - 4, wy - 34, ww / 2, wy - 24, ww / 2, wy)
        ctx.curve_to(ww / 2, wy + 30, hw / 2, hy - 30, hw / 2, hy)
        ctx.line_to(-hw / 2, hy)
        ctx.curve_to(-hw / 2, hy - 30, -ww / 2, wy + 30, -ww / 2, wy)
        ctx.curve_to(-ww / 2, wy - 24, -sw / 2 + 4, wy - 34, -sw / 2, sy + 34)
        ctx.close_path()
        outline = ctx.copy_path()
        top, dark = self.top_color, shade(self.top_color, 0.2)
        ctx.set_source(lit(ctx, top))
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        outfit = s["outfit"]
        if outfit == "blazer":  # open over a top, with lapels
            ctx.move_to(-30, sy - 10)
            ctx.line_to(30, sy - 10)
            ctx.line_to(8, hy)
            ctx.line_to(-8, hy)
            ctx.close_path()
            paint(ctx, self.under, 0)
            for side in (-1, 1):
                ctx.move_to(side * 30, sy - 10)
                ctx.line_to(side * 44, sy + 70)
                ctx.line_to(side * 6, sy + 118)
                ctx.close_path()
                paint(ctx, dark, 2)
        elif outfit in ("bomber", "leather"):  # a short jacket worn open
            ctx.rectangle(-28, sy - 10, 56, TORSO + 20)
            paint(ctx, self.under, 0)
            ctx.set_source_rgba(*dark)
            for side in (-1, 1):
                ctx.rectangle(side * 28 - 4, sy - 10, 8, TORSO + 20)
                ctx.fill()
            if outfit == "bomber":  # knitted hem and collar
                ctx.rectangle(-sw, hy - 20, 2 * sw, 24)
                ctx.fill()
                ctx.rectangle(-28, hy - 20, 56, 24)
                paint(ctx, self.under, 0)
                for side in (-1, 1):
                    ctx.move_to(side * 20, sy - 10)
                    ctx.line_to(side * 46, sy - 2)
                    ctx.line_to(side * 30, sy + 40)
                    ctx.close_path()
                    paint(ctx, dark, 2)
            else:  # wide lapels, a zip, and the dress under it
                for side in (-1, 1):
                    ctx.move_to(side * 26, sy - 10)
                    ctx.line_to(side * 58, sy + 30)
                    ctx.line_to(side * 28, sy + 92)
                    ctx.close_path()
                    paint(ctx, tint(top, 0.14), 2)
                rrect(ctx, -22, sy - 16, 44, 30, 8)
                paint(ctx, self.skin, 0)
        elif outfit == "cardigan":  # over a shirt and tie
            ctx.move_to(-28, sy - 10)
            ctx.line_to(28, sy - 10)
            ctx.line_to(4, sy + 124)
            ctx.line_to(-4, sy + 124)
            ctx.close_path()
            paint(ctx, self.under, 0)
            ctx.move_to(-8, sy + 4)
            ctx.line_to(8, sy + 4)
            ctx.line_to(11, sy + 96)
            ctx.line_to(0, sy + 112)
            ctx.line_to(-11, sy + 96)
            ctx.close_path()
            paint(ctx, hexc("7a2f3a"), 2)
            for side in (-1, 1):
                ctx.move_to(0, sy + 16)
                ctx.line_to(side * 28, sy - 10)
                ctx.line_to(side * 32, sy + 22)
                ctx.close_path()
                paint(ctx, tint(self.under, 0.4), 2)
            ctx.set_source_rgba(*dark)
            ctx.rectangle(-3, sy + 124, 6, TORSO)
            ctx.fill()
            for q in range(2):
                ellipse(ctx, 12, sy + 140 + q * 24, 5, 5)
                ctx.fill()
        elif outfit == "blouse":  # a wrap top tucked into high trousers
            ctx.rectangle(-sw, wy + 4, 2 * sw, TORSO)
            paint(ctx, self.bottom, 0)
            ctx.move_to(-24, sy - 10)
            ctx.line_to(24, sy - 10)
            ctx.line_to(0, sy + 52)
            ctx.close_path()
            paint(ctx, self.skin, 0)
            ctx.set_source_rgba(*dark)
            ctx.set_line_width(3)
            ctx.move_to(24, sy - 10)
            ctx.line_to(-ww / 2, wy)
            ctx.stroke()
        elif outfit == "turtleneck":
            ctx.set_source_rgba(*dark)
            ctx.set_line_width(2)
            for q in range(-3, 4):
                ctx.move_to(q * 18, sy + 30)
                ctx.line_to(q * 17, hy)
            ctx.stroke()
        if s.get("chain") or s.get("necklace"):
            ctx.set_source_rgba(*GOLD)
            ctx.set_line_width(3)
            ctx.new_sub_path()
            ctx.arc(0, sy - 30, 52 if s.get("chain") else 40, math.pi * 0.3, math.pi * 0.7)
            ctx.stroke()
        side = -self.inner  # the band of shadow down the side that is turned away
        ctx.rectangle(sw * 0.27 if side > 0 else -sw * 0.27 - 2 * sw, sy - 10, 2 * sw, TORSO + 30)
        ctx.set_source_rgba(0, 0, 0, 0.07)
        ctx.fill()
        ctx.rectangle(-sw, sy - 12, 2 * sw, 26)  # the chin's shadow
        ctx.set_source_rgba(0, 0, 0, 0.1)
        ctx.fill()
        ctx.restore()
        ctx.append_path(outline)
        ctx.set_source_rgba(*shade(top, 0.42)[:3], 0.5)
        ctx.set_line_width(1.6)
        ctx.stroke()
        if outfit == "turtleneck":
            rrect(ctx, -22, sy - 32, 44, 34, 10)
            paint(ctx, top)

    def _arm(self, ctx, side):
        px, py = self._shoulder(side)
        up, fore = self._arm_angles(side)
        thick = 36 if self.sw > 135 else 28
        elbow, wrist = thick * 0.84, thick * 0.62
        sleeve = self.top_color
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(-side * up)
        ellipse(ctx, 0, 0, thick * 0.56, thick * 0.56)  # the shoulder
        paint(ctx, sleeve, 0)
        ctx.move_to(-thick / 2, 0)
        ctx.line_to(thick / 2, 0)
        ctx.line_to(elbow / 2, UPPER_ARM)
        ctx.line_to(-elbow / 2, UPPER_ARM)
        ctx.close_path()
        paint(ctx, sleeve)
        ctx.translate(0, UPPER_ARM)
        ctx.rotate(-side * (fore - up))
        if ("in" if side == self.inner else "out") not in self.pocket:
            ellipse(ctx, -side * wrist * 0.42, FOREARM + 6, wrist * 0.22, wrist * 0.42)  # thumb
            paint(ctx, self.skin, 0)
            ellipse(ctx, 0, FOREARM + 11, wrist * 0.52, wrist * 0.78)
            paint(ctx, self.skin)
        ctx.move_to(-elbow / 2, 0)
        ctx.line_to(elbow / 2, 0)
        ctx.line_to(wrist / 2, FOREARM)
        ctx.line_to(-wrist / 2, FOREARM)
        ctx.close_path()
        paint(ctx, sleeve)
        ellipse(ctx, 0, 0, elbow / 2, elbow / 2)  # one arm, not two pieces
        paint(ctx, sleeve, 0)
        ctx.restore()

    # ---------- head ----------

    def _crown(self, ctx, pts, grow=1.1):
        """Hair on top of the head down to the hairline `pts`, which runs right to left in head units."""
        ctx.save()
        ellipse(ctx, 0, -0.12 * U, 0.9 * U * grow, 1.04 * U * grow)
        ctx.clip()
        ctx.new_path()
        ctx.move_to(-1.5 * U, -1.7 * U)
        ctx.line_to(1.5 * U, -1.7 * U)
        for x, y in pts:
            ctx.line_to(x * U, y * U)
        ctx.close_path()
        paint(ctx, self.hair)
        ctx.set_source_rgba(*tint(self.hair, 0.5)[:3], 0.3)
        ctx.set_line_width(0.1 * U)
        ctx.set_line_cap(1)
        ctx.new_sub_path()
        ctx.arc(0, 0.45 * U, 1.3 * U, math.pi * 1.3, math.pi * 1.52)
        ctx.stroke()
        ctx.set_line_cap(0)
        ctx.restore()

    def _strand(self, ctx, side, down, wide=0.2):
        """Hair falling past the face on one side."""
        ctx.move_to(side * 0.6 * U, -0.6 * U)
        ctx.curve_to(side * 1.08 * U, -0.2 * U, side * 1.04 * U, down * 0.6 * U, side * 0.86 * U, down * U)
        ctx.curve_to(side * (0.86 - wide) * U, down * 0.5 * U, side * 0.84 * U, 0.0, side * 0.6 * U, -0.6 * U)
        paint(ctx, self.hair, 2.5)

    def _hair_back(self, ctx):
        look, sway = self.spec["look"], self.sway
        if look == "pony":  # a high ponytail, swinging behind the shoulder turned away
            side = -self.inner
            ctx.save()
            ctx.translate(side * 0.3 * U, -1.0 * U)
            ctx.rotate(sway * 0.5)
            ctx.move_to(0, -0.1 * U)
            ctx.curve_to(side * 1.3 * U, -0.3 * U, side * 1.5 * U, 1.2 * U, side * 0.9 * U, 2.5 * U)
            ctx.curve_to(side * 0.86 * U, 1.4 * U, side * 0.7 * U, 0.6 * U, 0, 0.5 * U)
            ctx.close_path()
            paint(ctx, shade(self.hair, 0.1))
            ctx.restore()
            ellipse(ctx, 0, -0.2 * U, 0.98 * U, 1.1 * U)
            paint(ctx, self.hair)
        elif look == "bob":
            ctx.move_to(-1.0 * U, -0.3 * U)
            ctx.curve_to(-1.22 * U, -1.5 * U, 1.22 * U, -1.5 * U, 1.0 * U, -0.3 * U)
            ctx.curve_to(1.16 * U, 0.4 * U, 1.14 * U, 0.9 * U, 0.84 * U, 1.04 * U)
            ctx.line_to(-0.84 * U, 1.04 * U)
            ctx.curve_to(-1.14 * U, 0.9 * U, -1.16 * U, 0.4 * U, -1.0 * U, -0.3 * U)
            paint(ctx, shade(self.hair, 0.12))
        elif look in ("quiff", "curtain"):
            high = 1.74 if look == "quiff" else 1.56
            ctx.move_to(-0.92 * U, -0.2 * U)
            ctx.curve_to(-1.08 * U, -high * U, 1.08 * U, -high * U, 0.92 * U, -0.2 * U)
            ctx.close_path()
            paint(ctx, self.hair)
        elif look == "curls":
            for q in range(13):
                a = math.pi * (0.86 + q * 1.28 / 12)
                ellipse(ctx, math.cos(a) * 1.08 * U, -0.42 * U + math.sin(a) * 1.02 * U, 0.46 * U, 0.46 * U)
                paint(ctx, self.hair)
            ellipse(ctx, 0, -0.5 * U, 1.2 * U, 1.14 * U)
            paint(ctx, self.hair, 0)
        elif look == "bald":
            for side in (-1, 1):
                ellipse(ctx, side * 0.86 * U, -0.02 * U, 0.14 * U, 0.34 * U)
                paint(ctx, self.hair)

    def _eye(self, ctx, x, y, side, blink, lx, ly, lid):
        wide = self.eyes == "wide"
        woman = self.spec.get("woman")
        ctx.set_line_cap(1)
        if self.eyes in ("happy", "shut"):  # closed in a laugh, or screwed shut in pain
            ctx.set_source_rgba(*self.line)
            ctx.set_line_width(4)
            ctx.new_sub_path()
            if self.eyes == "happy":
                ctx.arc(x, y + 0.14 * U, 0.2 * U, math.pi * 1.18, math.pi * 1.82)
            else:
                ctx.move_to(x - side * 0.2 * U, y + 0.03 * U)
                ctx.line_to(x + side * 0.02 * U, y - 0.04 * U)
                ctx.line_to(x + side * 0.2 * U, y + 0.06 * U)
            ctx.stroke()
            return
        w = 0.2 * U
        open_ = (1 - 0.6 * lid) if not wide else 1.0
        up, down = (0.2 if wide else 0.135) * U * blink * open_, (0.09 if wide else 0.06) * U * blink
        rise = 0.035 * U  # the outer corner sits a touch higher
        y_in, y_out = y + rise * 0.5, y - rise * 0.5
        x_in, x_out = x - side * w, x + side * w

        def upper(ctx):
            ctx.move_to(x_in, y_in)
            ctx.curve_to(x - side * w * 0.5, y - up * 1.5, x + side * w * 0.5, y - up * 1.5, x_out, y_out)
        upper(ctx)
        ctx.curve_to(x + side * w * 0.5, y + down * 1.7, x - side * w * 0.5, y + down * 1.7, x_in, y_in)
        ctx.close_path()
        ctx.set_source_rgba(0.98, 0.97, 0.95, 1)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        r = (0.09 if wide else 0.108) * U
        ix, iy = x + lx * w * 0.42, y - 0.02 * U + ly * 0.07 * U
        ellipse(ctx, ix, iy, r, r)
        ctx.set_source_rgba(*shade(self.iris, 0.25))
        ctx.fill()
        ellipse(ctx, ix, iy + r * 0.2, r * 0.8, r * 0.7)
        ctx.set_source_rgba(*tint(self.iris, 0.18))
        ctx.fill()
        ellipse(ctx, ix, iy, r * 0.45, r * 0.45)
        ctx.set_source_rgba(*INK)
        ctx.fill()
        ellipse(ctx, ix - r * 0.38, iy - r * 0.4, r * 0.28, r * 0.28)
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.fill()
        ctx.rectangle(x - w, y - up * 1.5, 2 * w, up * 0.8)  # the lid's shadow
        ctx.set_source_rgba(*INK[:3], 0.2)
        ctx.fill()
        ctx.restore()
        ctx.set_source_rgba(*self.line)
        ctx.set_line_width(4.5 if woman else 3.2)
        upper(ctx)
        ctx.stroke()
        if not wide:  # the crease of the lid
            ctx.set_source_rgba(*shade(self.skin, 0.3))
            ctx.set_line_width(2)
            ctx.move_to(x_in + side * w * 0.2, y - 0.2 * U)
            ctx.curve_to(x, y - 0.26 * U, x + side * w * 0.6, y - 0.24 * U, x_out, y_out - 0.1 * U)
            ctx.stroke()
        if woman and blink > 0.5:
            ctx.set_source_rgba(*self.line)
            ctx.set_line_width(3.5)
            ctx.move_to(x_out, y_out)
            ctx.line_to(x_out + side * 0.11 * U, y_out - 0.09 * U)
            ctx.stroke()

    def _head(self, ctx, t, c):
        s, look = self.spec, self.spec["look"]
        man = not s.get("woman")
        ox, oy = c["look_x"] * U * 0.14, c["look_y"] * U * 0.08
        gx, gy = self.gaze[0] * U * 0.02, self.gaze[1] * U * 0.02

        for side in (-1, 1):  # ears
            ellipse(ctx, side * 0.87 * U - ox * 0.3, 0.16 * U, 0.1 * U, 0.17 * U)
            paint(ctx, shade(self.skin, 0.06), 2.5)
            if s.get("hoops"):
                ctx.set_source_rgba(*GOLD)
                ctx.set_line_width(4)
                ctx.new_sub_path()
                ctx.arc(side * 0.9 * U - ox * 0.3, 0.52 * U, 0.19 * U, 0, 2 * math.pi)
                ctx.stroke()
            elif s.get("woman"):
                ellipse(ctx, side * 0.9 * U - ox * 0.3, 0.36 * U, 0.045 * U, 0.045 * U)
                ctx.set_source_rgba(*GOLD)
                ctx.fill()
        jaw = 0.64 if man else 0.48  # a wider jaw on the men
        ctx.new_path()
        ctx.move_to(-0.86 * U, -0.1 * U)
        ctx.curve_to(-0.92 * U, -1.2 * U, 0.92 * U, -1.2 * U, 0.86 * U, -0.1 * U)
        ctx.curve_to(0.86 * U, 0.6 * U, jaw * U, 1.08 * U, 0, 1.13 * U)
        ctx.curve_to(-jaw * U, 1.08 * U, -0.86 * U, 0.6 * U, -0.86 * U, -0.1 * U)
        ctx.close_path()
        face = ctx.copy_path()
        g = cairo.RadialGradient(-0.3 * U, -0.35 * U, 0.2 * U, 0, 0, 1.5 * U)
        g.add_color_stop_rgba(0, *tint(self.skin, 0.14))
        g.add_color_stop_rgba(0.55, *self.skin)
        g.add_color_stop_rgba(1, *shade(self.skin, 0.24))
        ctx.set_source(g)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        for side in (-1, 1):  # the eye sockets, softly
            ellipse(ctx, side * 0.4 * U + ox, 0.08 * U + oy, 0.3 * U, 0.2 * U)
            ctx.set_source_rgba(*shade(self.skin, 0.3)[:3], 0.16)
            ctx.fill()
        if s.get("beard"):
            ctx.rectangle(-U, 0.42 * U + oy, 2 * U, U)
            ctx.set_source_rgba(*self.hair)
            ctx.fill()
            ellipse(ctx, ox * 0.9, 0.8 * U + oy, 0.24 * U, 0.12 * U)
            ctx.set_source_rgba(*self.skin)
            ctx.fill()
        elif s.get("stubble"):
            ctx.rectangle(-U, 0.5 * U, 2 * U, U)
            ctx.set_source_rgba(*INK[:3], 0.12)
            ctx.fill()
        ctx.restore()
        ctx.append_path(face)
        ctx.set_source_rgba(*shade(self.skin, 0.42)[:3], 0.5)
        ctx.set_line_width(1.6)
        ctx.stroke()

        # hair in front
        if look == "pony":  # swept back from a side parting
            self._crown(ctx, [(1.5, 0.1), (0.93, 0.06), (0.84, -0.4), (0.4, -0.74), (-0.2, -0.86), (-0.5, -0.62), (-0.82, -0.3), (-0.93, 0.06), (-1.5, 0.1)])
            self._strand(ctx, self.inner, 0.7, 0.12)
        elif look == "bob":  # a blunt fringe
            self._crown(ctx, [(1.5, 0.3), (0.92, 0.2), (0.86, -0.28), (0.5, -0.34), (0.1, -0.28), (-0.4, -0.36), (-0.86, -0.28), (-0.92, 0.2), (-1.5, 0.3)])
            for side in (-1, 1):
                self._strand(ctx, side, 0.98, 0.26)
        elif look == "quiff":  # short at the sides, pushed up in front
            self._crown(ctx, [(1.5, -0.3), (0.9, -0.34), (0.78, -0.62), (0.4, -0.7), (0.0, -0.66), (-0.4, -0.72), (-0.78, -0.62), (-0.9, -0.34), (-1.5, -0.3)], 1.12)
            ctx.save()
            ctx.translate(self.inner * 0.16 * U, -1.08 * U)
            ctx.rotate(self.inner * -0.2)
            ellipse(ctx, 0, 0, 0.66 * U, 0.36 * U)
            paint(ctx, self.hair)
            ctx.set_source_rgba(*tint(self.hair, 0.16))
            ctx.set_line_width(4)
            for q in (-1, 0, 1):
                ctx.move_to(q * 0.26 * U - 0.1 * U, 0.2 * U)
                ctx.curve_to(q * 0.26 * U, -0.1 * U, q * 0.3 * U + 0.1 * U, -0.2 * U, q * 0.3 * U + 0.2 * U, -0.22 * U)
            ctx.stroke()
            ctx.restore()
        elif look == "curtain":
            self._crown(ctx, [(1.5, 0.0), (0.93, 0.04), (0.82, -0.3), (0.46, -0.58), (0.06, -0.86), (0, -1.0), (-0.06, -0.86), (-0.46, -0.58),
                              (-0.82, -0.3), (-0.93, 0.04), (-1.5, 0.0)], 1.12)
        elif look == "curls":
            self._crown(ctx, [(1.5, -0.3), (0.9, -0.3), (0.7, -0.62), (0.4, -0.5), (0.1, -0.7), (-0.2, -0.52), (-0.5, -0.66), (-0.9, -0.3), (-1.5, -0.3)], 1.14)
            if s.get("band"):  # a scarf tied round the hair
                ctx.set_source_rgba(*hexc(s["band"]))
                ctx.set_line_width(0.2 * U)
                ctx.new_sub_path()
                ctx.arc(0, 0.2 * U, 1.12 * U, math.pi * 1.22, math.pi * 1.78)
                ctx.stroke()

        ex, ey = 0.4 * U, 0.12 * U
        blush = max(c["blush"], 0.3 if s.get("woman") else 0.0)
        if blush > 0.05:
            ctx.set_source_rgba(0.9, 0.35, 0.4, 0.24 * blush)
            for side in (-1, 1):
                ellipse(ctx, side * 0.56 * U + ox * 0.6, 0.46 * U + oy * 0.5, 0.17 * U, 0.09 * U)
                ctx.fill()
        if s.get("freckles"):
            ctx.set_source_rgba(*shade(self.skin, 0.28))
            for side in (-1, 1):
                for fx, fy in ((0.44, 0.4), (0.56, 0.46), (0.5, 0.52), (0.64, 0.4)):
                    ellipse(ctx, side * fx * U + ox * 0.6, fy * U + oy * 0.5, 2, 2)
                    ctx.fill()
        if s.get("mole"):
            ellipse(ctx, -0.44 * U + ox * 0.8, 0.62 * U + oy * 0.6, 1.8, 1.8)
            ctx.set_source_rgba(*shade(self.skin, 0.6))
            ctx.fill()
        blink = 1.0
        if 0 <= t - self.blink_t < BLINK:
            blink = 1 - 0.9 * math.sin(math.pi * (t - self.blink_t) / BLINK) ** 0.6
        lx, ly = c["look_x"] + self.gaze[0], c["look_y"] + self.gaze[1]
        for side in (-1, 1):
            self._eye(ctx, side * ex + ox + gx, ey + oy + gy, side, blink, lx, ly, c["lid"])
        ctx.set_line_cap(1)
        if s.get("glasses"):
            ctx.set_source_rgba(1, 1, 1, 0.12)
            for side in (-1, 1):
                ellipse(ctx, side * ex + ox, ey + oy, 0.3 * U, 0.3 * U)
                ctx.fill()
            ctx.set_source_rgba(*INK)
            ctx.set_line_width(3.5)
            for side in (-1, 1):
                ctx.new_sub_path()
                ctx.arc(side * ex + ox, ey + oy, 0.3 * U, 0, 2 * math.pi)
            ctx.move_to(-ex + ox + 0.3 * U, ey + oy)
            ctx.line_to(ex + ox - 0.3 * U, ey + oy)
            ctx.stroke()
        # brows: they carry most of the expression; one can go up on its own
        tilt, lift = c["brow"], c["raise"]
        ctx.set_source_rgba(*self.line)
        ctx.set_line_width(6 if man else 4)
        for side in (-1, 1):
            up = lift * 0.1 * U + (c["cock"] * 0.13 * U if side == self.inner else 0.0)
            x, y = side * ex + ox, ey + oy - 0.36 * U - up
            ctx.move_to(x - side * 0.22 * U, y + tilt * 0.12 * U + 0.02 * U)
            ctx.curve_to(x - side * 0.04 * U, y - 0.05 * U, x + side * 0.12 * U, y - 0.06 * U - tilt * 0.04 * U,
                         x + side * 0.26 * U, y - tilt * 0.07 * U + 0.03 * U)
            ctx.stroke()
        # nose: a short line and its shadow
        turn = 1 if c["look_x"] >= 0 else -1
        nx, ny = ox * 1.2, 0.5 * U + oy
        ctx.move_to(nx + turn * 0.02 * U, ny - 0.36 * U)
        ctx.line_to(nx + turn * 0.14 * U, ny + 0.02 * U)
        ctx.line_to(nx - turn * 0.02 * U, ny + 0.03 * U)
        ctx.close_path()
        ctx.set_source_rgba(*shade(self.skin, 0.3)[:3], 0.3)
        ctx.fill()
        ellipse(ctx, nx, ny, 0.1 * U, 0.075 * U)
        ctx.set_source_rgba(*tint(self.skin, 0.1))
        ctx.fill()
        ctx.set_source_rgba(*shade(self.skin, 0.36))
        ctx.set_line_width(2.4)
        ctx.new_sub_path()
        ctx.arc(nx, ny - 0.01 * U, 0.1 * U, math.pi * 0.2, math.pi * 0.8)
        ctx.stroke()

        mx, my = ox * 0.9, 0.8 * U + oy * 0.7
        lips = hexc(s.get("lips", "a8454f")) if s.get("woman") else shade(self.skin, 0.42)
        m = self.mouth
        if self.talk_cur <= 0.06 and m in ("smile", "flat", "smirk", "sad", "wobbly"):  # the lower lip
            ellipse(ctx, mx, my + 0.055 * U, 0.11 * U, 0.05 * U)
            ctx.set_source_rgba(*lips[:3], 0.75 if s.get("woman") else 0.3)
            ctx.fill()
            ellipse(ctx, mx - 0.03 * U, my + 0.045 * U, 0.04 * U, 0.016 * U)
            ctx.set_source_rgba(1, 1, 1, 0.3)
            ctx.fill()
        ctx.set_source_rgba(*lips)
        ctx.set_line_width(4)
        if self.talk_cur > 0.06:
            ellipse(ctx, mx, my, (0.14 - 0.03 * self.talk_cur) * U, (0.02 + 0.1 * self.talk_cur) * U)
            ctx.set_source_rgba(*MOUTH)
            ctx.fill_preserve()
            ctx.set_source_rgba(*lips)
            ctx.set_line_width(2.5)
            ctx.stroke()
        elif m == "smile":
            ctx.move_to(mx - 0.15 * U, my - 0.03 * U)
            ctx.curve_to(mx - 0.06 * U, my + 0.05 * U, mx + 0.06 * U, my + 0.05 * U, mx + 0.15 * U, my - 0.03 * U)
            ctx.stroke()
        elif m == "smirk":  # one corner up
            d = self.inner
            ctx.move_to(mx - d * 0.13 * U, my + 0.02 * U)
            ctx.curve_to(mx - d * 0.02 * U, my + 0.04 * U, mx + d * 0.08 * U, my + 0.01 * U, mx + d * 0.16 * U, my - 0.07 * U)
            ctx.stroke()
        elif m == "grin":
            ctx.move_to(mx - 0.19 * U, my - 0.05 * U)
            ctx.line_to(mx + 0.19 * U, my - 0.05 * U)
            ctx.curve_to(mx + 0.12 * U, my + 0.13 * U, mx - 0.12 * U, my + 0.13 * U, mx - 0.19 * U, my - 0.05 * U)
            ctx.close_path()
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.fill_preserve()
            ctx.set_source_rgba(*lips)
            ctx.set_line_width(3)
            ctx.stroke()
        elif m == "open":
            ellipse(ctx, mx, my + 2, 0.08 * U, 0.11 * U)
            ctx.set_source_rgba(*MOUTH)
            ctx.fill()
        elif m == "sad":
            ctx.move_to(mx - 0.13 * U, my + 0.04 * U)
            ctx.curve_to(mx - 0.05 * U, my - 0.04 * U, mx + 0.05 * U, my - 0.04 * U, mx + 0.13 * U, my + 0.04 * U)
            ctx.stroke()
        elif m == "wobbly":  # pressed tight, uneven
            ctx.move_to(mx - 0.13 * U, my + 0.01 * U)
            ctx.line_to(mx - 0.04 * U, my - 0.02 * U)
            ctx.line_to(mx + 0.05 * U, my + 0.02 * U)
            ctx.line_to(mx + 0.13 * U, my - 0.01 * U)
            ctx.stroke()
        else:
            ctx.move_to(mx - 0.11 * U, my)
            ctx.line_to(mx + 0.11 * U, my)
            ctx.stroke()
        ctx.set_line_cap(0)
        if s.get("beard"):  # moustache
            for side in (-1, 1):
                ctx.save()
                ctx.translate(ox * 1.1 + side * 0.15 * U, 0.66 * U + oy)
                ctx.rotate(side * 0.25)
                ellipse(ctx, 0, 0, 0.19 * U, 0.07 * U)
                paint(ctx, shade(self.hair, 0.1), 2)
                ctx.restore()
        if self.tears:
            for side in (-1, 1):
                fall = (t * 0.7 + (side + 1) * 0.25) % 1
                ellipse(ctx, side * (ex + 0.08 * U) + ox, ey + oy + 0.2 * U + fall * 0.7 * U, 0.04 * U, 0.07 * U)
                ctx.set_source_rgba(0.62, 0.83, 0.92, 1 - fall * 0.7)
                ctx.fill()
