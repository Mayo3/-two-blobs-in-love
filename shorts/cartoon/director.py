"""Turns script beats into animation. Each script line gets one or more actions
(e.g. "point_bird", "hold_hands"); every frame resets the couple to a neutral pose,
applies the current action, and the blobs ease toward the result.

Actions are a fixed vocabulary, so an AI writing scripts can only pick from what
we know looks good.
"""
import math

import cairo

from . import props as P
from .characters import Blob
from .draw import clamp, ease, ease_out_back, hexc, puff
from .scenes import GROUND, H, W, Scene

AX, BX = 360, 720
STAGE_LIFT = 320  # the whole cartoon sits higher so the caption line fits below it
STAGE_ZOOM = 1.22  # and is zoomed in around the couple's feet so they fill the frame
OFFSTAGE = 1350
FOCUS = (540, GROUND - 230)  # camera zooms around the couple's faces
CLOSE_UP = 0.07  # extra zoom on every other beat
PUSH_IN = 0.025  # slow zoom over the length of a beat
GLIDE = 2.5  # how quickly the camera eases to a new framing
BOUNCE = 0.28  # seconds of squash-and-stretch when a beat starts
HOOK_CLOUD = 232  # size of the cloud behind the hook title
WORD_BOB = 0.03  # squash on every spoken word
EMPH_STRETCH = 0.09  # stretch up on *highlighted* words

ACTIONS = {}


def action(name, desc):
    def deco(fn):
        ACTIONS[name] = (fn, desc)
        return fn
    return deco


def describe_actions():
    """Vocabulary for the script-writing prompt."""
    return "\n".join(f"- {k}: {v[1]}" for k, v in ACTIONS.items())


def timed_beats(beats, line_times):
    """beats[i] is an action string or list of strings for script line i.
    Returns [{start, end, name, arg}] with sub-beats splitting the line evenly."""
    out = []
    for (start, end), b in zip(line_times, beats):
        parts = b if isinstance(b, list) else [b]
        step = (end - start) / len(parts)
        for k, part in enumerate(parts):
            name, _, arg = part.partition(":")
            if name not in ACTIONS:
                raise ValueError(f"unknown action '{name}'")
            out.append({"start": start + k * step, "end": start + (k + 1) * step, "name": name, "arg": arg})
    return out


class Animator:
    def __init__(self, scene, beats, words=(), hook=None):
        self.scene = Scene(scene)
        self.beats = beats
        self.hook = hook  # (seconds, centre y) of the cloud behind the hook title, or None
        self.words = [w for w in words if w.get("start") is not None]  # caption tokens with timings
        self.A = Blob("A", "ff9a8b", "sprout", AX, GROUND, 330, +1, seed=1)
        self.B = Blob("B", "b9a3f5", "bow", BX, GROUND, 312, -1, seed=2)
        self.B.twin_color = self.A.base_color
        self.B.twin_accessory = "sprout"
        self.S = Blob("S", "c9c6d3", None, OFFSTAGE, GROUND, 310, -1, seed=3)
        self.monitor = 0.3
        self.monitor_t = 0.3
        self.zoom = 1.0

    def frame(self, ctx, t, dt):
        A, B, S = self.A, self.B, self.S
        A.reset(AX)
        B.reset(BX)
        S.reset(OFFSTAGE)
        S.mouth = "flat"
        S.tgt["look_x"] = -0.5
        self.monitor_t = 0.3
        self.back, self.front = [], []
        index, lt, dur = 0, t, 1.0
        for index, b in enumerate(self.beats):
            if b["start"] <= t < b["end"] or (b is self.beats[-1] and t >= b["start"]):
                fn = ACTIONS[b["name"]][0]
                dur = b["end"] - b["start"]
                lt = t - b["start"]
                fn(self, lt, clamp(lt / max(dur, 0.01)), dur, b["arg"])
                break
        if lt < BOUNCE:  # both react to every new beat with a little squash and stretch
            for blob in (A, B):
                blob.tgt["squash"] += 0.07 * math.sin(math.pi * lt / BOUNCE)
        self.move_to_speech(t)
        for blob in (A, B, S):
            blob.update(dt, t)
        self.monitor += (self.monitor_t - self.monitor) * (1 - math.exp(-3 * dt))

        ctx.set_source_rgba(*self.scene.floor)
        ctx.paint()
        ctx.save()
        ctx.translate(W / 2, GROUND - STAGE_LIFT)
        ctx.scale(STAGE_ZOOM, STAGE_ZOOM)
        ctx.translate(-W / 2, -GROUND)
        self.camera(ctx, dt, index, lt, dur)
        self.scene.draw(ctx, t, self)
        for f in self.back:
            f(ctx)
        S.draw(ctx, t)
        A.draw(ctx, t)
        B.draw(ctx, t)
        for f in self.front:
            f(ctx)
        ctx.restore()
        if self.hook and t < self.hook[0]:
            self.hook_cloud(ctx, t, *self.hook)

    def hook_cloud(self, ctx, t, seconds, y):
        """Puffy white cloud the hook title sits in: pops in, floats, fades as the title goes."""
        pop = 0.75 + 0.25 * ease_out_back(min(1, t * 3.5))
        fade = clamp((seconds - t) / 0.25)
        ctx.save()
        ctx.translate(W / 2, y + 14 + math.sin(t * 2.2) * 6)  # the bumps sit high, so centre the body on the text
        ctx.scale(pop * 1.3, pop)  # wider than tall, room for three lines of text
        ctx.push_group()
        puff(ctx, 0, 0, HOOK_CLOUD, hexc("fffaf7"))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade)
        ctx.restore()

    def move_to_speech(self, t):
        """Blobs bob on every spoken word; on highlighted words they stretch up, throw
        their free arms up and sparkle. Added on top of whatever the action does."""
        word = next((w for w in self.words if w["start"] <= t < w["end"]), None)
        if word is None:
            return
        p = clamp((t - word["start"]) / max(word["end"] - word["start"], 0.05))
        on_stage = [b for b in (self.A, self.B) if b.tgt["x"] != OFFSTAGE]
        for b in on_stage:
            b.tgt["squash"] += WORD_BOB * math.sin(math.pi * p)
        if not word["emph"]:
            return
        for b in on_stage:
            b.tgt["squash"] -= EMPH_STRETCH * math.sin(math.pi * p)
            if b.tgt["arm_out"] < 40:  # only arms the action isn't already using
                b.tgt["arm_out"] = 125
            if b.eyes == "open":
                b.eyes = "wide"
        lt = t - word["start"]
        self.front.append(lambda ctx: P.sparkles(ctx, lt, 540, 1250, spread=300))

    def camera(self, ctx, dt, index, lt, dur):
        """Calm framing: every other beat glides to a closer shot, and each beat pushes in slowly."""
        target = 1 + (CLOSE_UP if index % 2 else 0) + PUSH_IN * clamp(lt / max(dur, 0.01))
        self.zoom += (target - self.zoom) * (1 - math.exp(-GLIDE * dt))
        ctx.translate(*FOCUS)
        ctx.scale(self.zoom, self.zoom)
        ctx.translate(-FOCUS[0], -FOCUS[1])

    # helpers used by actions
    def look_at_each_other(self, amount=0.85):
        self.A.tgt["look_x"] = amount
        self.B.tgt["look_x"] = -amount

    def look_viewer(self, *blobs):
        for b in blobs or (self.A, self.B):
            b.tgt["look_x"], b.tgt["look_y"] = 0.0, 0.25

    def hold(self, left, right, lx=365, rx=715):
        """Move two blobs together and angle their inner arms so the hands meet."""
        left.tgt["x"], right.tgt["x"] = lx, rx
        lw, rw = left.size / 2, right.size / 2
        gap = (right.cur["x"] - 0.82 * rw) - (left.cur["x"] + 0.82 * lw)
        for b, w in ((left, lw), (right, rw)):
            reach = clamp(gap / 2 / (0.42 * w), 0, 1)
            b.tgt["arm_in"] = math.degrees(math.asin(reach)) if gap > 0 else 15


# ---------- action vocabulary ----------

@action("idle", "the couple stands together, glancing at each other and at the viewer")
def _idle(an, lt, p, dur, arg):
    if int(lt / 2.2) % 2 == 1:
        an.look_viewer()


@action("wave", "A waves hello at the viewer (good for an opening line)")
def _wave(an, lt, p, dur, arg):
    an.A.tgt["arm_out"] = 150 + 25 * math.sin(lt * 9)
    an.A.mouth = "grin"
    an.look_viewer()


@action("hearts", "hearts float up between them")
def _hearts(an, lt, p, dur, arg):
    an.look_at_each_other()
    an.A.eyes = an.B.eyes = "happy"
    an.front.append(lambda ctx: P.hearts_rising(ctx, lt, 540, 1320))


@action("turn_toward", "they turn to each other, blush and smile; hearts rise")
def _turn_toward(an, lt, p, dur, arg):
    an.look_at_each_other(1.0)
    an.A.tgt["blush"] = an.B.tgt["blush"] = 1.0
    if p > 0.35:
        an.A.eyes = an.B.eyes = "happy"
        an.A.mouth = an.B.mouth = "grin"
    an.B.hop = 0.25 if p > 0.3 else 0
    an.front.append(lambda ctx: P.hearts_rising(ctx, lt - 0.3, 540, 1320))


@action("point_bird", "A points at a bird flying past; B looks up and smiles (arg 'ignore': B stays on the phone)")
def _point_bird(an, lt, p, dur, arg):
    A, B = an.A, an.B
    fly = max(dur, 3.0)
    bx = 1180 - (lt / fly) * 1450
    by = 1150 + math.sin(lt * 3) * 25
    A.tgt["arm_in"] = 150
    A.tgt["look_x"] = clamp((bx - A.cur["x"]) / 250, -1, 1)
    A.tgt["look_y"] = -0.8
    A.mouth = "open" if p < 0.4 else "grin"
    if arg == "ignore":
        _phone(an, lt)
    else:
        B.tgt["look_x"] = clamp((bx - B.cur["x"]) / 250, -1, 1) if p > 0.2 else -0.8
        B.tgt["look_y"] = -0.7 if p > 0.2 else 0
        B.mouth = "open" if 0.2 < p < 0.5 else "grin"
        if p > 0.6:
            an.front.append(lambda ctx: P.hearts_rising(ctx, lt - 0.6 * dur, 540, 1320, n=4))
    an.front.append(lambda ctx: P.bird(ctx, bx, by, lt))


@action("bid", "A reaches toward B with a little heart speech-bubble (asking for attention)")
def _bid(an, lt, p, dur, arg):
    an.look_at_each_other()
    an.A.tgt["arm_in"] = 55
    ax = an.A.cur["x"]
    an.front.append(lambda ctx: P.bubble(ctx, lt, ax + 90, 1165, "speech", "heart", tail_to=(ax + 40, 1330)))


def _phone(an, lt):
    B = an.B
    B.tgt["look_x"], B.tgt["look_y"] = -0.3, 0.9
    B.tgt["arm_in"] = 70
    B.mouth = "flat"
    bx = B.cur["x"]
    an.front.append(lambda ctx: P.phone(ctx, bx - 125, GROUND - 235, lt))


@action("ignore", "B stares at their phone; A droops sadly under a little rain cloud")
def _ignore(an, lt, p, dur, arg):
    _phone(an, lt)
    A = an.A
    A.mouth = "sad"
    A.tgt["lean"] = -5
    A.tgt["look_x"] = 0.8
    A.tgt["blush"] = 0
    ax = A.cur["x"]
    if p > 0.2:
        an.front.append(lambda ctx: P.rain_cloud(ctx, lt - 0.2 * dur, ax, 1160, lt))


@action("shrug", "both shrug, arms up, with question marks")
def _shrug(an, lt, p, dur, arg):
    for b in (an.A, an.B):
        b.tgt["arm_in"] = b.tgt["arm_out"] = 118
        b.mouth = "flat"
    an.look_viewer()
    an.front.append(lambda ctx: P.floating_marks(ctx, lt, 540, 1190))


@action("hug", "they squeeze into a hug; a big heart pops")
def _hug(an, lt, p, dur, arg):
    an.A.tgt["x"], an.B.tgt["x"] = 440, 640
    an.A.tgt["arm_in"] = an.B.tgt["arm_in"] = 80
    an.A.eyes = an.B.eyes = "happy"
    an.A.tgt["blush"] = an.B.tgt["blush"] = 1
    an.A.tgt["squash"] = an.B.tgt["squash"] = 0.04
    an.front.append(lambda ctx: P.heart_pop(ctx, lt - 0.25, 540, 1210))


@action("hold_hands", "they walk together and hold hands; a small heart pops")
def _hold_hands(an, lt, p, dur, arg):
    an.hold(an.A, an.B)
    an.look_at_each_other(0.6)
    an.A.tgt["blush"] = an.B.tgt["blush"] = 0.8
    an.monitor_t = 0.1
    an.front.append(lambda ctx: P.heart_pop(ctx, lt - 0.45, 540, 1250, size=42))


@action("scared", "a storm cloud with lightning appears; both shiver")
def _scared(an, lt, p, dur, arg):
    for b in (an.A, an.B):
        b.tgt["shiver"] = 1
        b.eyes = "wide"
        b.mouth = "wobbly"
        b.tgt["look_y"] = -0.6
        b.tgt["arm_out"] = 35
        b.tgt["blush"] = 0
    an.monitor_t = 1.0
    an.back.append(lambda ctx: P.storm(ctx, lt, 540, 1160, lt, ease(lt * 2)))


@action("alone", "B walks off; A is left alone, nervous")
def _alone(an, lt, p, dur, arg):
    an.B.tgt["x"] = OFFSTAGE
    A = an.A
    A.tgt["x"] = 450
    A.tgt["shiver"] = 0.8
    A.eyes = "wide"
    A.mouth = "wobbly"
    A.tgt["blush"] = 0
    an.monitor_t = 0.95
    an.back.append(lambda ctx: P.storm(ctx, lt, 450, 1160, lt, 0.6))


@action("stranger", "a grey stranger walks in and holds A's hand; A is only a bit calmer")
def _stranger(an, lt, p, dur, arg):
    an.B.tgt["x"] = OFFSTAGE
    an.hold(an.A, an.S)
    an.A.tgt["shiver"] = 0.35
    an.A.mouth = "flat"
    an.A.tgt["look_x"] = 0.6
    an.A.tgt["blush"] = 0
    an.monitor_t = 0.6


@action("calm", "holding hands, eyes closed happily, sparkles around (fear melts away)")
def _calm(an, lt, p, dur, arg):
    _hold_hands(an, lt + 1, p, dur, arg)
    an.A.eyes = an.B.eyes = "happy"
    an.monitor_t = 0.0
    an.back.append(lambda ctx: P.sparkles(ctx, lt, 540, 1280, spread=260))


@action("nervous", "B is nervous and sweating while A talks a lot (speech bubble)")
def _nervous(an, lt, p, dur, arg):
    B, A = an.B, an.A
    B.tgt["shiver"] = 0.5
    B.sweat = True
    B.eyes = "wide"
    B.mouth = "wobbly"
    B.tgt["blush"] = 0
    A.tgt["arm_out"] = 100 + 30 * math.sin(lt * 7)
    A.mouth = "open" if int(lt * 6) % 2 else "grin"
    an.look_at_each_other()
    ax = A.cur["x"]
    an.front.append(lambda ctx: P.bubble(ctx, lt, ax - 10, 1165, "speech", "dots", tail_to=(ax + 10, 1330)))


@action("think", "a thought bubble with a question mark; both look up, curious")
def _think(an, lt, p, dur, arg):
    for b in (an.A, an.B):
        b.tgt["look_y"] = -0.8
        b.mouth = "flat"
    an.A.tgt["look_x"], an.B.tgt["look_x"] = 0.3, -0.3
    an.front.append(lambda ctx: P.bubble(ctx, lt, 560, 1170, "thought", arg or "?", tail_to=(420, 1330)))


@action("photo", "camera flash, a polaroid of the couple appears (arg: a short label like '1987')")
def _photo(an, lt, p, dur, arg):
    an.look_viewer()
    an.A.mouth = an.B.mouth = "grin"
    old = an.A.cur["old"] > 0.5
    an.front.append(lambda ctx: P.polaroid(ctx, lt, 830, 1175, 0.12, arg or "us", old=old))
    an.front.append(lambda ctx: P.flash(ctx, lt, W, H + STAGE_LIFT))


@action("compare", "two polaroids (then / now) side by side with a magnifying glass sweeping over them")
def _compare(an, lt, p, dur, arg):
    for b in (an.A, an.B):
        b.tgt["look_y"] = -0.8
        b.mouth = "open"
    mx = 280 + (math.sin(lt * 1.6) * 0.5 + 0.5) * 520
    an.front.append(lambda ctx: P.polaroid(ctx, lt, 280, 1175, -0.1, "then"))
    an.front.append(lambda ctx: P.polaroid(ctx, lt - 0.25, 800, 1175, 0.1, "now", old=True))
    an.front.append(lambda ctx: P.magnifier(ctx, mx, 1130))


@action("old", "both age: grey hair and round glasses (stays until 'young')")
def _old(an, lt, p, dur, arg):
    an.A.persist["old"] = an.B.persist["old"] = 1.0
    an.A.tgt["old"] = an.B.tgt["old"] = 1.0
    an.look_at_each_other()
    an.A.eyes = an.B.eyes = "happy"


@action("young", "back to their young selves")
def _young(an, lt, p, dur, arg):
    an.A.persist["old"] = an.B.persist["old"] = 0.0
    an.A.tgt["old"] = an.B.tgt["old"] = 0.0
    _hearts(an, lt, p, dur, arg)


@action("twin", "B morphs to look exactly like A (stays until 'unmatch')")
def _twin(an, lt, p, dur, arg):
    if p > 0.35:  # let viewers see B as themselves first, then the transformation
        an.B.persist["mix"] = 1.0
        an.B.tgt["mix"] = 1.0
        an.A.mouth = an.B.mouth = "open"
    an.look_at_each_other()
    an.back.append(lambda ctx: P.sparkles(ctx, lt, 540, 1350, spread=280))


@action("unmatch", "B turns back into their own colour; both laugh")
def _unmatch(an, lt, p, dur, arg):
    an.B.persist["mix"] = 0.0
    an.B.tgt["mix"] = 0.0
    an.look_at_each_other()
    an.A.mouth = an.B.mouth = "grin"
    an.A.eyes = an.B.eyes = "happy"


@action("ask_viewer", "both look at the viewer, A waves, question marks above (for a closing question)")
def _ask_viewer(an, lt, p, dur, arg):
    an.look_viewer()
    an.A.tgt["arm_out"] = 140 + 20 * math.sin(lt * 8)
    an.B.mouth = "open"
    an.front.append(lambda ctx: P.floating_marks(ctx, lt, 540, 1200, "?", "ff8fab"))


@action("watched", "a cute security camera in the corner watches them (being observed in a study)")
def _watched(an, lt, p, dur, arg):
    an.look_at_each_other()
    if int(lt / 1.8) % 2:
        an.A.tgt["look_x"], an.A.tgt["look_y"] = 1, -0.7
    an.front.append(lambda ctx: P.security_camera(ctx, 880, 1160, lt))


def render_frames(animator, duration, fps, write):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    n = int(round(duration * fps))
    for i in range(n):
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        animator.frame(ctx, i / fps, 1 / fps)
        surf.flush()
        write(bytes(surf.get_data()))
