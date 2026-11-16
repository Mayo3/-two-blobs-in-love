"""Turns a story into a little film. Unlike the two-blob director, any number of characters can
be on stage and the story moves from place to place: each line says where we are, who is there,
who speaks to whom and how everyone feels, and the stage cuts to the place, puts the people in it,
turns them to each other, frames them and acts the feelings out.

A line of a story:
  who    the speaker
  text   what they say (*stressed* words as in the blobs' scripts)
  to     "viewer" for an aside told to the camera (the others dim and freeze), or a name
  scene  a place from tales.sets; naming one (even the same one) cuts to a new shot, where everyone
         in `on` already stands. Without it the shot goes on and newcomers walk in from the side.
  stamp  with scene: a note shown for the whole shot ("3 years ago", "last night")
  memory with scene: true for something remembered; the shot is framed and tinted like a photo
  enter  with scene: names from `on` who walk in instead of already standing there
  shot   "close" for a close-up of the speaker on this line
  phone  {"from": name, "texts": [...]}: a phone held up to the viewer with messages on it, for this line
  hit    {"by": name, "on": name, "with": thing from PROPS}: halfway through the line one hits the other over
         the head with it (they must stand next to each other); follow it with the feeling "dazed"
  on     who is on stage, left to right; stays until a later line changes it
  acts   {name: feeling} from FEELINGS; lasting ones stay until changed, the rest pass with the line
  show   a picture from tales.icons (or a short text) in a bubble over the speaker
  sound  a sound the speaker makes first (chuckle, laugh, gasp, sigh, groan)
"""
import math
import os

import cairo

from shorts.cartoon.draw import clamp, ease_out_back, ellipse, hexc, rrect
from shorts.cartoon.scenes import GROUND, W

from . import icons
from .cast import CAST, INK, INK_HEX, REST_ARM, ROOT, Actor, paint
from .sets import Room

FONT = os.path.join(ROOT, "fonts", "Poppins-ExtraBold.ttf")
FONT_NAME = "Poppins ExtraBold"  # the same file, as the captions name it
PAPER = hexc("fffdf8")  # speech cards, bubbles, name tags

TAG_Y = 1322  # name tags sit here on screen, just above the caption line
ZOOM_MIN, ZOOM_MAX, WIDE_AT = 0.95, 1.2, 1560  # the wide shot, and where on screen the floor then sits
ZOOM_MID, MID_CHEST, MID_AT = 2.1, 400, 1010  # two people from the hips up: this far above the floor sits here on screen
ZOOM_CLOSE, CLOSE_AT = 3.3, 960  # a close-up of a face
GRADE = (0.1, 0.11, 0.2, 0.16)  # a cool veil over every place so the people stand out and the film looks less like a toy
CUT_PUNCH = 1.06  # a new shot starts a touch closer and settles
MARGIN = 220  # air left and right of the group when the camera frames it
GLIDE = 2.6  # how quickly the camera eases to a new framing
PUSH_IN = 0.03  # slow zoom over the length of a line
ASIDE_DARK = 0.42  # how far the scene dims while someone talks to the viewer
OFF_LEFT, OFF_RIGHT = -260, 1340
WORD_BOB = 0.02
EMPH_STRETCH = 0.04
TAG_HOLD = 2.6  # seconds a newcomer's name tag stays up
CARD_WIDE, CARD_ROW, CARD_PAD = 860, 96, 104  # the card the hook and the closing question are written on

FEELINGS = {}
LASTING = set()


def feeling(name, desc, lasting=False):
    def deco(fn):
        FEELINGS[name] = (fn, desc)
        if lasting:
            LASTING.add(name)
        return fn
    return deco


def describe_feelings():
    """Vocabulary for a script-writing prompt."""
    return "\n".join(f"- {k}: {v[1]}{' (stays until changed)' if k in LASTING else ''}" for k, v in FEELINGS.items())


_labels = {}


def label(text, size, color=INK_HEX):
    """`text` as a picture, set in the channel's own font straight from its file: Cairo can only
    use fonts installed on the machine, and the look must not depend on that. Returns (surface, width, height)."""
    key = (text, size, color)
    if key not in _labels:
        from PIL import Image, ImageDraw, ImageFont

        font = ImageFont.truetype(FONT, size)
        x0, y0, x1, y1 = font.getbbox(text)
        wide, high = x1 + 4, size + size // 2
        img = Image.new("L", (wide, high), 0)
        ImageDraw.Draw(img).text((2, 0), text, font=font, fill=255)
        r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
        data = bytearray()
        for a in img.tobytes():  # Cairo wants blue, green, red, alpha with the colour already multiplied by alpha
            data += bytes((b * a // 255, g * a // 255, r * a // 255, a))
        surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, wide, high, wide * 4)
        _labels[key] = (surf, wide, high)
    return _labels[key]


def slots(n):
    """Where n characters stand, left to right."""
    if n <= 1:
        return [540.0] * n
    step = {2: 290, 3: 300}.get(n, 690 / (n - 1))
    return [540 + (k - (n - 1) / 2) * step for k in range(n)]


def plan(lines, scene=None):
    """Per line: where we are, who is on stage and how each feels, with everything that carries over filled in."""
    out, on, mood = [], [], {}
    shot, stamp, memory = 0, None, False
    for line in lines:
        enter = []
        if "scene" in line:  # a cut
            shot += 1 if out else 0
            scene, stamp, memory, mood = line["scene"], line.get("stamp"), bool(line.get("memory")), {}
            enter = line.get("enter", [])
        if scene not in Room.kinds:
            raise ValueError(f"unknown scene '{scene}'")
        on = list(line.get("on", on))
        if line["who"] not in on:
            raise ValueError(f"{line['who']} speaks but is not on stage: {line['text']}")
        mood = {k: v for k, v in mood.items() if v in LASTING and k in on}
        mood.update(line.get("acts", {}))
        hit = line.get("hit")
        if hit and (hit["with"] not in PROPS or hit["by"] not in on or hit["on"] not in on
                    or abs(on.index(hit["by"]) - on.index(hit["on"])) != 1):
            raise ValueError(f"bad hit: {hit}")
        for name, f in mood.items():
            if f not in FEELINGS:
                raise ValueError(f"unknown feeling '{f}'")
            if name not in CAST:
                raise ValueError(f"unknown character '{name}'")
        out.append({"who": line["who"], "to": line.get("to"), "on": on, "mood": dict(mood), "show": line.get("show"),
                    "scene": scene, "shot": shot, "stamp": stamp, "memory": memory, "enter": enter,
                    "close": line.get("shot") == "close", "phone": line.get("phone"), "hit": line.get("hit")})
    return out


class Stage:
    def __init__(self, scene, lines, times, words=(), clouds=(), roles=None):
        self.plan = plan(lines, scene)
        self.rooms = {k: Room(k) for k in {p["scene"] for p in self.plan}}
        self.line, self.cut_t, self.flash, self.shake = None, 0.0, False, 0.0
        self.times = times  # (start, end) of every line
        self.words = [w for w in words if w.get("start") is not None]
        self.clouds = clouds
        self.roles = roles or {}
        self.actors, self.first = {}, {}
        for i, p in enumerate(self.plan):
            xs = slots(len(p["on"]))
            for name, x in zip(p["on"], xs):
                if name not in self.actors:
                    off = OFF_LEFT if x < 540 else OFF_RIGHT
                    a = Actor(name, x if i == 0 else off, GROUND, seed=len(self.actors) + 11)
                    a.off = off
                    self.actors[name] = a
                    self.first[name] = self.times[i][0]
        self.zoom, self.cx, self.dark, self.cam = None, 540.0, 0.0, None
        self.light = cairo.RadialGradient(260, 520, 100, 400, 800, 1700)
        self.light.add_color_stop_rgba(0, 1, 0.95, 0.82, 0.16)
        self.light.add_color_stop_rgba(0.45, 1, 0.95, 0.82, 0.0)
        self.light.add_color_stop_rgba(1, 0.05, 0.06, 0.14, 0.34)

    # ---------- one frame ----------

    def frame(self, ctx, t, dt):
        i = next((k for k, (s, e) in enumerate(self.times) if s <= t < e), len(self.times) - 1)
        p = self.plan[i]
        start, end = self.times[i]
        lt, dur = t - start, max(end - start, 0.01)
        last = i == len(self.plan) - 1
        on = [self.actors[n] for n in p["on"]]
        speaker = self.actors[p["who"]]
        clouded = any(c["start"] <= t < c["end"] for c in self.clouds)
        aside = p["to"] == "viewer" and not last and len(on) > 1
        self.back, self.front, self.now = [], [], t
        wide = clouded or bool(p["phone"] or p["show"])  # something to look at up top: step back so no head is behind it

        for a in self.actors.values():
            a.reset(a.off)
        for a, x in zip(on, slots(len(on))):
            a.reset(x)
            a.off = OFF_LEFT if x < 540 else OFF_RIGHT
        if i != self.line:
            if self.line is None or p["shot"] != self.plan[self.line]["shot"]:  # a cut: everyone is in place at once
                for a in self.actors.values():
                    a.cur["x"] = a.off if a.key in p["enter"] else a.tgt["x"]
                self.flash = self.line is not None and (p["memory"] or self.plan[self.line]["memory"])
                self.zoom, self.cut_t, self.dark = None, t, ASIDE_DARK if aside else 0.0
            self.line = i
        room = self.rooms[p["scene"]]
        target = self.actors.get(p["to"]) if p["to"] in p["on"] else None
        if target is None and len(on) > 1:
            target = min((a for a in on if a is not speaker), key=lambda a: abs(a.tgt["x"] - speaker.tgt["x"]))
        for a in on:
            other = target if a is speaker else speaker
            toward = (1 if other.tgt["x"] > a.tgt["x"] else -1) if other and other is not a else (1 if a.tgt["x"] < 540 else -1)
            a.inner = toward
            a.tgt["look_x"] = 0.8 * toward
            if abs(a.tgt["x"] - a.cur["x"]) > 40:  # walking to their place
                a.hop = 0.6
            name = p["mood"].get(a.key, "calm")
            if not (aside and a is not speaker):  # during an aside the others hold still
                FEELINGS[name][0](self, a, lt, clamp(lt / dur), toward)
            else:
                FEELINGS[name if name in LASTING else "calm"][0](self, a, 0.0, 0.0, toward)
        if p["to"] == "viewer" or len(on) == 1:
            speaker.tgt["look_x"], speaker.tgt["look_y"] = 0.0, 0.25
        self.shake = 0.0
        if p["hit"]:
            self.strike(p["hit"], lt, hit_time(start, end) - start)
        if last:  # the closing question is everyone's: all turn to the viewer
            for a in on:
                a.tgt["look_x"], a.tgt["look_y"] = 0.0, 0.25
        self.speak(t, speaker)
        if p["show"] and not clouded and not p["phone"]:
            self.bubble(speaker, p["show"], lt, dur)
        for a in self.actors.values():
            a.update(dt, t)

        k = 1 - math.exp(-5 * dt)
        self.dark += ((ASIDE_DARK if aside else 0.0) - self.dark) * k
        ctx.set_source_rgba(*room.floor)
        ctx.paint()
        pair = [self.actors[p["hit"]["by"]], self.actors[p["hit"]["on"]]] if p["hit"] else on  # a blow is seen from near
        self.camera(ctx, dt, pair, speaker if speaker in pair else pair[0], aside, wide, lt / dur, p["close"])
        room.draw(ctx, t, self)
        ctx.save()
        ctx.identity_matrix()
        ctx.set_source_rgba(*GRADE)
        ctx.paint()
        ctx.set_source(self.light)  # a lamp somewhere up to the left, the far corner in shade
        ctx.paint()
        ctx.restore()
        for f in self.back:
            f(ctx)
        lit = [speaker] if self.dark > 0.02 else []
        for a in sorted(self.actors.values(), key=lambda a: a is speaker):
            if a not in lit:
                a.draw(ctx, t)
        if lit:
            ctx.save()
            ctx.identity_matrix()
            ctx.set_source_rgba(*INK[:3], self.dark)
            ctx.paint()
            ctx.restore()
            speaker.draw(ctx, t)
        for f in self.front:
            f(ctx)
        ctx.restore()
        if p["memory"]:
            memory_frame(ctx)
        if self.flash and t - self.cut_t < 0.35:  # into and out of a memory through a flash of white
            ctx.set_source_rgba(1, 1, 1, 1 - (t - self.cut_t) / 0.35)
            ctx.paint()
        vignette(ctx)
        if p["phone"]:
            phone_chat(ctx, p["phone"], lt, dur)
        if p["stamp"] and not clouded and not p["phone"]:
            stamp(ctx, p["stamp"], t - self.cut_t)
        for c in self.clouds:
            if c["start"] <= t < c["end"]:
                self.card(ctx, t, c, speaker)
        self.tags(ctx, t, on, speaker, i)

    def speak(self, t, speaker):
        """The speaker's mouth moves with the words and they bob on each one; on *stressed*
        words they stretch up and throw a hand in the air."""
        now = next((w for w in self.words if w["start"] <= t < w["end"]), None)
        if not now:
            return
        p = clamp((t - now["start"]) / max(now["end"] - now["start"], 0.05))
        beats = max(1, round(len(now["text"]) / 3.2))
        speaker.talk = (0.3 + 0.7 * abs(math.sin(math.pi * p * beats))) * min(1, 6 * p, 6 * (1 - p) + 0.25)
        speaker.tgt["squash"] += WORD_BOB * math.sin(math.pi * p)
        if now["emph"]:
            speaker.tgt["squash"] -= EMPH_STRETCH * math.sin(math.pi * p)
            if (speaker.tgt["ua_out"], speaker.tgt["fa_out"]) == REST_ARM:  # a free hand comes up with the word
                arm(speaker, "out", 22, 118)
            speaker.tgt["raise"] = max(speaker.tgt["raise"], 0.5)

    def bubble(self, speaker, what, lt, dur):
        """A picture of what the line is about, in a bubble over the speaker."""
        x = clamp(speaker.cur["x"] + speaker.inner * 70, 230, 850)
        y = speaker.top() - 150
        tail = (speaker.cur["x"] + speaker.inner * 20, speaker.top() - 14)

        def draw(ctx):
            s = ease_out_back(min(1, lt * 3.5)) * clamp((dur - lt) * 6)
            if s <= 0.01:
                return
            ctx.save()
            ctx.translate(x, y + math.sin(lt * 2.4) * 4)
            ctx.scale(s, s)
            for dy, col in ((10, (*INK[:3], 0.16)), (0, PAPER)):  # a soft shadow, then the paper
                rrect(ctx, -112, -84 + dy, 224, 168, 34)
                ctx.move_to(-22, 80 + dy)
                ctx.line_to((tail[0] - x) * 0.9, (tail[1] - y) * 0.9 + dy)
                ctx.line_to(22, 80 + dy)
                ctx.set_source_rgba(*col)
                ctx.fill()
            icons.draw(ctx, what, lt)
            ctx.restore()
        self.front.append(draw)

    def camera(self, ctx, dt, on, speaker, aside, wide, p, close=False):
        """Frame the shot as a film would: two people from the hips up, a crowd (or a card to read) in
        full, a close-up on the face; a little nearer to whoever talks to the viewer."""
        left = min(a.tgt["x"] - a.dims()[0] for a in on)
        right = max(a.tgt["x"] + a.dims()[0] for a in on)
        cx = (left + right) / 2
        if close and not wide:
            cx, cy, at, zoom = speaker.tgt["x"], speaker.head_y() + 50, CLOSE_AT, ZOOM_CLOSE
        elif wide or len(on) > 2:
            cy, at, zoom = GROUND, WIDE_AT, clamp(W / (right - left + MARGIN), ZOOM_MIN, ZOOM_MAX)
            cx += (speaker.tgt["x"] - cx) * 0.12
        else:
            cy, at, zoom = GROUND - MID_CHEST, MID_AT, ZOOM_MID * (1.1 if aside else 1.0)
            cx += (speaker.tgt["x"] - cx) * (0.55 if aside else 0.12)
        zoom *= 1 + PUSH_IN * p
        want = [zoom, cx, cy, at]
        if self.zoom is None:
            self.cam = [zoom * CUT_PUNCH, cx, cy, at]
        k = 1 - math.exp(-GLIDE * dt)
        self.cam = [v + (w - v) * k for v, w in zip(self.cam, want)]
        self.zoom = self.cam[0]
        half = W / 2 / self.zoom
        self.cx = self.cam[1] = clamp(self.cam[1], min(half, W / 2), max(W - half, W / 2))  # never show past the edge of the scene
        ctx.save()
        jolt = 16 * self.shake
        ctx.translate(W / 2 + jolt * math.sin(self.now * 90), self.cam[3] + jolt * math.cos(self.now * 70))
        ctx.scale(self.zoom, self.zoom)
        ctx.translate(-self.cx, -self.cam[2])

    def strike(self, hit, lt, when):
        """One hits the other over the head: the arm goes back, comes down at `when` seconds into the line,
        the picture jolts and the one who was hit sees stars."""
        a, b = self.actors[hit["by"]], self.actors[hit["on"]]
        d = 1 if b.tgt["x"] > a.tgt["x"] else -1
        a.inner, b.inner = d, -d
        a.tgt["look_x"], a.tgt["brow"], a.tgt["cock"], a.mouth = 0.8 * d, 0.9, 0.0, "flat"
        landed = lt >= when
        if not landed:
            arm(a, "in", 34, 172)
            a.tgt["lean"] = -4 * d
        else:
            arm(a, "in", 104, 114)
            a.tgt["lean"] = 7 * d
            a.tgt["x"] += d * 62
            if lt - when < 0.07:  # a blow is fast: no easing into it
                for key in ("ua_in", "fa_in", "x", "lean"):
                    a.cur[key] = a.tgt[key]
            FEELINGS["dazed"][0](self, b, lt - when, 0.0, -d)
            b.tgt["x"] += d * 26
            self.shake = clamp(1 - (lt - when) / 0.3)
            if lt - when < 0.45:
                x, y = b.cur["x"], b.top() + 20
                self.front.append(lambda ctx: bang(ctx, x, y, lt - when))
        hx, hy = a.hand_pos(d)
        fore = a._arm_angles(d)[1]
        self.front.append(lambda ctx: PROPS[hit["with"]](ctx, hx, hy, -d * fore, d))

    def screen_x(self, x):
        return W / 2 + (x - self.cx) * self.zoom

    def card(self, ctx, t, c, speaker):
        """The paper card the hook and the closing question are written on, with a tail to whoever says it."""
        pop = 0.8 + 0.2 * ease_out_back(min(1, (t - c["start"]) * 3.5)) if c["pop"] else 1.0
        fade = clamp((c["end"] - t) / 0.25) if c["fade"] else 1.0
        high = CARD_PAD + CARD_ROW * c["rows"]
        tail = clamp(self.screen_x(speaker.cur["x"]) - W / 2, -CARD_WIDE / 2 + 110, CARD_WIDE / 2 - 110)
        ctx.save()
        ctx.translate(W / 2, c["y"])
        ctx.scale(pop, pop)
        ctx.push_group()
        for dy, col in ((12, (*INK[:3], 0.18)), (0, PAPER)):
            rrect(ctx, -CARD_WIDE / 2, -high / 2 + dy, CARD_WIDE, high, 44)
            ctx.move_to(tail - 34, high / 2 - 2 + dy)
            ctx.line_to(tail + 34, high / 2 - 2 + dy)
            ctx.line_to(tail + (12 if tail < 0 else -12), high / 2 + 54 + dy)
            ctx.close_path()
            ctx.set_source_rgba(*col)
            ctx.fill()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade)
        ctx.restore()

    def tags(self, ctx, t, on, speaker, i):
        """Name tags under the feet: on whoever is speaking, and on a newcomer for a moment
        together with who they are to the storyteller ("my brother")."""
        shown = []
        for a in on:
            new = t - self.first[a.key] < (max(TAG_HOLD, self.times[0][1]) if self.first[a.key] == 0 else TAG_HOLD)
            if a is speaker or new:
                shown.append((a, new))
        for a, new in shown:
            role = self.roles.get(a.key) if new else None
            name, wn, hn = label(a.spec["label"], 40, "ffffff" if a is speaker else INK_HEX)
            sub, wr, hr = label(role, 30, "6b6f86") if role else (None, 0, 0)
            left = wn + 44  # the name sits on the character's colour, who they are on paper beside it
            wide = left + (wr + 40 if role else 0)
            x = clamp(self.screen_x(a.cur["x"]), wide / 2 + 16, W - wide / 2 - 16)
            y = TAG_Y
            for dy, col in ((7, (*INK[:3], 0.18)), (0, PAPER)):
                rrect(ctx, x - wide / 2, y - 31 + dy, wide, 62, 20)
                ctx.set_source_rgba(*col)
                ctx.fill()
            if a is speaker:
                ctx.save()
                rrect(ctx, x - wide / 2, y - 31, wide, 62, 20)
                ctx.clip()
                ctx.rectangle(x - wide / 2, y - 31, left if role else wide, 62)
                ctx.set_source_rgba(*a.tag_color)
                ctx.fill()
                ctx.restore()
            ctx.set_source_surface(name, x - wide / 2 + 22, y - hn / 2 + 1)
            ctx.paint()
            if role:
                ctx.set_source_surface(sub, x - wide / 2 + left + 18, y - hr / 2 + 1)
                ctx.paint()


def memory_frame(ctx):
    """Something remembered: warm and a little faded, in the white border of a photo."""
    from shorts.cartoon.scenes import H

    ctx.set_source_rgba(1, 0.86, 0.6, 0.2)
    ctx.paint()
    ctx.rectangle(0, 0, W, H)
    rrect(ctx, 34, 250, W - 68, H - 500, 30)
    ctx.set_fill_rule(1)
    ctx.set_source_rgba(*PAPER)
    ctx.fill()
    ctx.set_fill_rule(0)


def stamp(ctx, text, age):
    """When this shot happened, on a slanted strip at the top."""
    words, wide, high = label(text.upper(), 42, "ffffff")
    ctx.save()
    ctx.translate(W / 2, 440)
    ctx.rotate(-0.04)
    s = max(0.05, ease_out_back(min(1, age * 4)))
    ctx.scale(s, s)
    for dy, col in ((8, (*INK[:3], 0.2)), (0, INK)):
        rrect(ctx, -wide / 2 - 34, -44 + dy, wide + 68, 88, 16)
        ctx.set_source_rgba(*col)
        ctx.fill()
    ctx.set_source_surface(words, -wide / 2, -high / 2 + 2)
    ctx.paint()
    ctx.restore()


def focus_lines(ctx, x, y, t, color=(0.17, 0.18, 0.26), strength=0.5):
    """Lines rushing in on (x, y) from all sides, as in a comic: a shock."""
    import random

    rng = random.Random(int(t * 12))
    ctx.set_source_rgba(*color, strength)
    for k in range(34):
        a = k / 34 * 2 * math.pi + rng.uniform(-0.05, 0.05)
        near, wide = rng.uniform(300, 420), rng.uniform(0.012, 0.04)
        ctx.move_to(x + math.cos(a) * near, y + math.sin(a) * near)
        ctx.line_to(x + math.cos(a - wide) * 1700, y + math.sin(a - wide) * 1700)
        ctx.line_to(x + math.cos(a + wide) * 1700, y + math.sin(a + wide) * 1700)
        ctx.close_path()
    ctx.fill()


def gloom(ctx, x, top, lt):
    """Dark lines hanging over a head: shame, dread."""
    for k in range(7):
        long = (70 + 40 * math.sin(k * 2.3)) * clamp(lt * 4)
        ctx.set_source_rgba(0.2, 0.22, 0.4, 0.55)
        ctx.set_line_width(7)
        ctx.set_line_cap(1)
        ctx.move_to(x - 96 + k * 32, top - 70)
        ctx.line_to(x - 96 + k * 32, top - 70 + long)
        ctx.stroke()
    ctx.set_line_cap(0)


def sparkles(ctx, x, y, lt):
    """Four-pointed stars twinkling around someone pleased with themselves."""
    for k, (dx, dy, size) in enumerate(((-150, -40, 34), (150, -70, 42), (-110, 90, 24), (130, 70, 28), (0, -150, 30))):
        s = size * max(0.0, math.sin(lt * 5 + k * 1.4))
        if s < 2:
            continue
        cx, cy = x + dx, y + dy
        ctx.move_to(cx, cy - s)
        for q in range(4):
            a = q * math.pi / 2 - math.pi / 2
            ctx.line_to(cx + math.cos(a) * s, cy + math.sin(a) * s)
            ctx.line_to(cx + math.cos(a + math.pi / 4) * s * 0.28, cy + math.sin(a + math.pi / 4) * s * 0.28)
        ctx.close_path()
        ctx.set_source_rgba(1, 0.95, 0.6, 1)
        ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.9)
        ctx.set_line_width(3)
        ctx.stroke()


def hit_time(start, end):
    """When in a line with a hit the blow lands (the sound is put there too)."""
    return start + min(0.55 * (end - start), max(0.5, end - start - 0.9))


def bang(ctx, x, y, age):
    """The flash where a blow lands, and the word for it."""
    grow = ease_out_back(min(1, age * 9))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(grow, grow)
    ctx.rotate(-0.15)
    for q in range(20):
        r = 96 if q % 2 else 46
        a = q / 20 * 2 * math.pi
        ctx.line_to(math.cos(a) * r, math.sin(a) * r * 0.8)
    ctx.close_path()
    ctx.set_source_rgba(1, 0.86, 0.3, clamp(2 - age * 4.5))
    ctx.fill()
    word, wide, high = label("BONK", 44)
    ctx.set_source_surface(word, -wide / 2, -high / 2)
    ctx.paint_with_alpha(clamp(2 - age * 4.5))
    ctx.restore()


def stars(ctx, x, y, t):
    """Stars going round a head that has just been hit."""
    for q in range(4):
        a = t * 4 + q * math.pi / 2
        sx, sy = x + math.cos(a) * 62, y + math.sin(a) * 16
        if math.sin(a) < -0.2:
            continue  # behind the head
        ctx.new_sub_path()
        for i in range(10):
            r = 15 if i % 2 == 0 else 6
            b = i / 10 * 2 * math.pi - math.pi / 2 + t * 3
            ctx.line_to(sx + math.cos(b) * r, sy + math.sin(b) * r)
        ctx.close_path()
        ctx.set_source_rgba(1, 0.86, 0.3, 1)
        ctx.fill_preserve()
        ctx.set_source_rgba(0.8, 0.6, 0.1, 0.8)
        ctx.set_line_width(1.5)
        ctx.stroke()


def _held(ctx, x, y, angle):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)


def _bouquet(ctx, x, y, angle, d):
    _held(ctx, x, y, angle)
    ctx.move_to(-10, -6)
    ctx.line_to(10, -6)
    ctx.line_to(26, 58)
    ctx.line_to(-26, 58)
    ctx.close_path()
    paint(ctx, hexc("f4ece2"))
    for q, (fx, fy, col) in enumerate(((-24, 70, "f3c9cf"), (0, 60, "e5989b"), (24, 70, "ffffff"), (-12, 92, "ffffff"), (14, 94, "f3c9cf"), (0, 82, "c8553d"))):
        ellipse(ctx, fx, fy, 19, 19)
        paint(ctx, hexc(col))
    ctx.restore()


def _folder(ctx, x, y, angle, d):
    _held(ctx, x, y, angle)
    rrect(ctx, -14, -12, 28, 112, 5)
    paint(ctx, hexc("3d405b"))
    rrect(ctx, -10, -6, 20, 100, 3)
    paint(ctx, hexc("f1ece4"), 0)
    rrect(ctx, -14, 10, 28, 30, 3)
    paint(ctx, hexc("c8553d"))
    ctx.restore()


def _handbag(ctx, x, y, angle, d):
    _held(ctx, x, y, angle)
    ctx.set_source_rgba(*hexc("7a4a2a"))
    ctx.set_line_width(7)
    ctx.new_sub_path()
    ctx.arc(0, 26, 24, math.pi, 2 * math.pi)
    ctx.stroke()
    rrect(ctx, -40, 22, 80, 60, 12)
    paint(ctx, hexc("b5673a"))
    rrect(ctx, -40, 22, 80, 22, 10)
    paint(ctx, hexc("96512b"))
    ellipse(ctx, 0, 44, 7, 7)
    paint(ctx, hexc("e2b84d"))
    ctx.restore()


def _pan(ctx, x, y, angle, d):
    _held(ctx, x, y, angle)
    rrect(ctx, -7, -8, 14, 62, 6)
    paint(ctx, hexc("2b2d42"))
    ellipse(ctx, 0, 92, 46, 42)
    paint(ctx, hexc("4a4e69"))
    ellipse(ctx, 0, 92, 36, 32)
    paint(ctx, hexc("33364a"), 0)
    ctx.restore()


PROPS = {"bouquet": _bouquet, "folder": _folder, "handbag": _handbag, "pan": _pan}


def vignette(ctx):
    """Darker toward the edges, as through a lens."""
    from shorts.cartoon.scenes import H

    g = cairo.RadialGradient(W / 2, H * 0.48, 520, W / 2, H * 0.48, 1250)
    g.add_color_stop_rgba(0, 0.05, 0.05, 0.1, 0)
    g.add_color_stop_rgba(1, 0.05, 0.05, 0.1, 0.42)
    ctx.set_source(g)
    ctx.paint()


def phone_chat(ctx, chat, lt, dur):
    """A phone held up to the viewer: the messages somebody was not meant to see, arriving one by one."""
    rows = []
    for text in chat["texts"]:
        line, lines = "", []
        for word in text.split():
            if line and len(line) + len(word) > 21:
                lines.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        rows.append(lines + [line])
    wide, top = 580, 372
    high = 150 + sum(len(r) * 44 + 44 for r in rows)
    x0 = W / 2 - wide / 2
    ctx.save()
    ctx.translate(W / 2, top + high / 2)
    ctx.rotate(-0.025)
    pop = 0.85 + 0.15 * ease_out_back(min(1, lt * 4))
    ctx.scale(pop, pop)
    ctx.translate(-W / 2, -(top + high / 2))
    for dy, col in ((14, (*INK[:3], 0.25)), (0, INK)):
        rrect(ctx, x0, top + dy, wide, high, 52)
        ctx.set_source_rgba(*col)
        ctx.fill()
    rrect(ctx, x0 + 14, top + 14, wide - 28, high - 28, 40)
    ctx.set_source_rgba(*hexc("f3f4f8"))
    ctx.fill()
    name, wn, hn = label(chat["from"], 36)
    ctx.set_source_surface(name, W / 2 - wn / 2, top + 30)
    ctx.paint()
    ctx.rectangle(x0 + 14, top + 96, wide - 28, 3)
    ctx.set_source_rgba(*hexc("dfe1ea"))
    ctx.fill()
    y = top + 120
    gap = min(1.0, dur * 0.45 / len(rows))
    for k, lines in enumerate(rows):
        shown = clamp((lt - 0.3 - k * gap) * 6)
        if shown <= 0:
            break
        pics = [label(text, 32) for text in lines]
        rrect(ctx, x0 + 40, y, max(p[1] for p in pics) + 52, len(lines) * 44 + 26, 26)
        ctx.set_source_rgba(*hexc("e1e4ee", shown))
        ctx.fill()
        for j, (pic, _, _) in enumerate(pics):
            ctx.set_source_surface(pic, x0 + 66, y + 11 + j * 44)
            ctx.paint_with_alpha(shown)
        y += len(lines) * 44 + 44
    ctx.restore()


def question_marks(ctx, lt, x, y):
    """Question marks rising over the one who asks the viewer."""
    mark, wide, high = label("?", 64, "e63946")
    for k in range(3):
        age = lt - k * 0.35
        if age < 0:
            continue
        ctx.save()
        ctx.translate(x + (k - 1) * 50, y - (age % 1.6) * 60)
        ctx.rotate((k - 1) * 0.25)
        ctx.set_source_surface(mark, -wide / 2, -high / 2)
        ctx.paint_with_alpha(clamp(1 - (age % 1.6) / 1.6))
        ctx.restore()


def glass(ctx, x, y, t):
    """A glass of red, held by the stem."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(0.08 * math.sin(t * 1.3))
    ctx.set_source_rgba(1, 1, 1, 0.85)
    ctx.set_line_width(4)
    ctx.move_to(0, 4)
    ctx.line_to(0, -30)
    ctx.move_to(-14, 4)
    ctx.line_to(14, 4)
    ctx.stroke()
    ctx.move_to(-20, -78)
    ctx.curve_to(-22, -44, -10, -30, 0, -30)
    ctx.curve_to(10, -30, 22, -44, 20, -78)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, 0.3)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.85)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.move_to(-20, -58)
    ctx.curve_to(-18, -40, -9, -32, 0, -32)
    ctx.curve_to(9, -32, 18, -40, 20, -58)
    ctx.close_path()
    ctx.set_source_rgba(*hexc("7a1f2e"))
    ctx.fill()
    ctx.restore()


def phone(ctx, x, y, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.15)
    rrect(ctx, -24, -42, 48, 84, 10)
    ctx.set_source_rgba(*INK)
    ctx.fill()
    rrect(ctx, -18, -34, 36, 66, 5)
    glow = 0.75 + 0.25 * math.sin(t * 5)
    ctx.set_source_rgba(0.6 * glow, 0.85 * glow, 1 * glow, 1)
    ctx.fill()
    ctx.restore()


# ---------- feelings: how one character holds themselves during a line ----------
# fn(stage, actor, seconds into the line, 0..1 through the line, +1 / -1 toward whoever they face)

def arm(a, which, upper, fore):
    """Pose one arm ("in": the one toward the other person, "out": the one away). Angles as in Actor.reset."""
    a.tgt[f"ua_{which}"], a.tgt[f"fa_{which}"] = upper, fore


def crossed(a):
    arm(a, "in", 14, -108)
    arm(a, "out", 14, -98)


def hand_on_hip(a, which="out"):
    arm(a, which, 40, -55)


def holding_self(a):
    """One arm across the body, gripping the other: ill at ease."""
    arm(a, "out", 10, -78)


@feeling("calm", "listening or talking normally", lasting=True)
def _calm(st, a, lt, p, toward):
    if a.spec["outfit"] in ("bomber", "turtleneck"):  # the men stand with a hand in a pocket
        arm(a, "out", 12, -14)
        a.pocket.add("out")


@feeling("happy", "pleased: a real smile", lasting=True)
def _happy(st, a, lt, p, toward):
    a.mouth = "grin"
    a.tgt["lid"], a.tgt["cock"], a.tgt["brow"] = 0.15, 0.0, -0.2
    a.tgt["blush"] = 0.5


@feeling("laugh", "laughs out loud, head back, a hand on the stomach")
def _laugh(st, a, lt, p, toward):
    a.mouth, a.eyes = "grin", "happy"
    a.tgt["tip"] = -6 * toward
    a.tgt["lean"] = -3 * toward
    a.tgt["squash"] += 0.05 * math.sin(lt * 15)
    arm(a, "in", 12, -92)


@feeling("smug", "pleased with themselves: arms crossed, a smirk, heavy lids", lasting=True)
def _smug(st, a, lt, p, toward):
    a.mouth = "smirk"
    a.tgt["lid"], a.tgt["cock"], a.tgt["brow"] = 0.5, 0.6, 0.0
    a.tgt["lean"] = -3 * toward
    a.tgt["tip"] = 3 * toward
    crossed(a)


@feeling("sarcastic", "says the opposite of what they mean: a hand on the hip, one brow up, a slow blink", lasting=True)
def _sarcastic(st, a, lt, p, toward):
    a.mouth = "smirk"
    a.tgt["lid"], a.tgt["cock"], a.tgt["brow"] = 0.55, 1.0, 0.0
    a.tgt["tip"] = 5 * toward
    hand_on_hip(a)
    if 0.25 < lt < 0.9:  # the eyes roll up and away
        a.tgt["look_y"], a.tgt["look_x"] = -0.9, -0.3 * toward


@feeling("deadpan", "no expression at all: says something terrible as if it were the weather", lasting=True)
def _deadpan(st, a, lt, p, toward):
    a.mouth = "flat"
    a.tgt["lid"], a.tgt["cock"], a.tgt["brow"], a.tgt["raise"] = 0.5, 0.0, 0.0, 0.0


@feeling("sip", "takes a slow sip of wine while everything burns", lasting=True)
def _sip(st, a, lt, p, toward):
    a.mouth = "smirk"
    a.tgt["lid"], a.tgt["cock"] = 0.45, 0.5
    drinking = (lt % 3.2) > 2.3
    if drinking:
        arm(a, "out", -16, -170)
        a.tgt["tip"] = -4 * toward
    else:
        arm(a, "out", 14, -128)
    x, y = a.hand_pos(-toward)
    st.front.append(lambda ctx: glass(ctx, x, y - 6, lt))


@feeling("proud", "shows something off: a fist by the shoulder, chin up")
def _proud(st, a, lt, p, toward):
    a.mouth = "grin"
    a.tgt["cock"], a.tgt["lid"] = 0.4, 0.2
    a.tgt["tip"] = -3 * toward
    arm(a, "out", 30, 158 + 6 * math.sin(lt * 9))


@feeling("angry", "furious: leaning in, brows down, hands on hips", lasting=True)
def _angry(st, a, lt, p, toward):
    a.mouth = "flat"
    a.tgt["brow"], a.tgt["lid"], a.tgt["cock"] = 1.0, 0.25, 0.0
    a.tgt["lean"] = 5 * toward
    hand_on_hip(a, "in")
    hand_on_hip(a, "out")


@feeling("annoyed", "unimpressed: arms crossed, brows down, a flat mouth", lasting=True)
def _annoyed(st, a, lt, p, toward):
    a.mouth = "flat"
    a.tgt["brow"], a.tgt["lid"], a.tgt["cock"] = 0.6, 0.4, 0.3
    crossed(a)


@feeling("point", "points at the one they are talking to, accusing")
def _point(st, a, lt, p, toward):
    a.mouth = "flat"
    a.tgt["brow"], a.tgt["cock"] = 0.8, 0.0
    a.tgt["lean"] = 4 * toward
    arm(a, "in", 72, 80 + 3 * math.sin(lt * 10))
    hand_on_hip(a)


@feeling("shocked", "eyes wide, brows up, a hand to the mouth")
def _shocked(st, a, lt, p, toward):
    a.eyes, a.mouth = "wide", "open"
    a.tgt["raise"], a.tgt["brow"], a.tgt["cock"], a.tgt["lid"] = 1.0, -0.2, 0.0, 0.0
    a.tgt["lean"] = -4 * toward
    arm(a, "out", -16, -172)
    if lt < 0.3:
        a.hop = 0.6


@feeling("nervous", "caught out: sweating, a tight mouth, eyes sliding away, gripping their own arm", lasting=True)
def _nervous(st, a, lt, p, toward):
    a.sweat = True
    a.mouth = "wobbly"
    a.tgt["shiver"] = 0.2
    a.tgt["brow"], a.tgt["raise"], a.tgt["cock"], a.tgt["lid"] = -0.7, 0.5, 0.0, 0.0
    holding_self(a)
    if int(lt * 1.6) % 2:
        a.tgt["look_x"] = -0.8 * toward


@feeling("guilty", "ashamed: looks at the floor, shoulders in", lasting=True)
def _guilty(st, a, lt, p, toward):
    a.mouth = "wobbly"
    a.tgt["look_y"] = 0.8
    a.tgt["brow"], a.tgt["cock"], a.tgt["lid"] = -0.8, 0.0, 0.3
    a.tgt["blush"] = 0.9
    a.tgt["tip"] = 4 * toward
    holding_self(a)


@feeling("sad", "hurt: head down, a sad mouth", lasting=True)
def _sad(st, a, lt, p, toward):
    a.mouth = "sad"
    a.tgt["brow"], a.tgt["cock"], a.tgt["lid"] = -1.0, 0.0, 0.35
    a.tgt["look_y"] = 0.5
    a.tgt["tip"] = 3 * toward


@feeling("cry", "in tears", lasting=True)
def _cry(st, a, lt, p, toward):
    _sad(st, a, lt, p, toward)
    a.mouth = "wobbly"
    a.tears = True
    a.tgt["shiver"] = 0.12
    arm(a, "out", -16, -172)


@feeling("plead", "begging: hands together in front of the chest, big eyes")
def _plead(st, a, lt, p, toward):
    a.eyes, a.mouth = "wide", "wobbly"
    a.tgt["brow"], a.tgt["raise"], a.tgt["cock"] = -1.0, 0.6, 0.0
    a.tgt["lean"] = 4 * toward
    arm(a, "in", 12, -140)
    arm(a, "out", 12, -140)


@feeling("shrug", "shrugs, palms up: so what?")
def _shrug(st, a, lt, p, toward):
    a.mouth = "smirk"
    a.tgt["raise"], a.tgt["cock"], a.tgt["lid"] = 0.6, 0.0, 0.3
    a.tgt["squash"] -= 0.04
    lift = 112 + 5 * math.sin(lt * 6)
    arm(a, "in", 20, lift)
    arm(a, "out", 20, lift)


@feeling("phone", "glued to their phone, smiling at it", lasting=True)
def _phone(st, a, lt, p, toward):
    a.tgt["look_x"], a.tgt["look_y"] = 0.2 * toward, 0.9
    a.tgt["lid"], a.tgt["tip"] = 0.4, 5 * toward
    a.mouth = "smirk"
    arm(a, "in", 14, -132)
    x, y = a.hand_pos(toward)
    st.front.append(lambda ctx: phone(ctx, x, y - 30, lt))


@feeling("dazed", "has just been hit on the head: eyes screwed shut, swaying, stars going round", lasting=True)
def _dazed(st, a, lt, p, toward):
    a.eyes, a.mouth = "shut", "wobbly"
    a.tgt["brow"], a.tgt["cock"], a.tgt["raise"] = -0.5, 0.0, 0.0
    a.tgt["tip"] = -14 * toward + 5 * math.sin(lt * 3)
    a.tgt["lean"] = -4 * toward + 2 * math.sin(lt * 2.2)
    arm(a, "out", 24, 20)
    x, y = a.cur["x"], a.top() + 14
    st.front.append(lambda ctx: stars(ctx, x, y, st.now))


@feeling("wave", "waves hello")
def _wave(st, a, lt, p, toward):
    a.mouth = "grin"
    arm(a, "out", 36, 150 + 14 * math.sin(lt * 9))
