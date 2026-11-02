"""The two mochi-blob mascots (and a grey stranger). All poses are smooth: actions set
targets each frame and the blob eases toward them."""
import math
import random

from .draw import OUTLINE, ellipse, fill_stroke, hexc, mix, rrect

SMOOTH = 9.0  # higher = snappier


class Blob:
    def __init__(self, name, color, accessory, x, ground, size, inner_side, seed=0):
        self.name = name
        self.base_color = hexc(color)
        self.accessory = accessory
        self.size = size
        self.inner = inner_side  # +1 if the partner is to the right
        self.ground = ground
        self.rng = random.Random(seed)
        self.next_blink = self.rng.uniform(1.0, 3.0)
        self.blink_t = -1.0
        self.twin_color = self.base_color
        self.twin_accessory = accessory
        # current values (smoothed) — persistent ones are never reset per frame
        self.cur = dict(x=x, look_x=0.0, look_y=0.0, arm_in=12.0, arm_out=12.0, lean=0.0, blush=0.0,
                        shiver=0.0, alpha=1.0, old=0.0, mix=0.0, squash=0.0)
        self.persist = {"old": 0.0, "mix": 0.0}
        self.reset(x)

    def reset(self, home_x):
        """Default targets at the start of every frame; actions override them."""
        self.tgt = dict(x=home_x, look_x=0.55 * self.inner, look_y=0.0, arm_in=12.0, arm_out=12.0, lean=0.0,
                        blush=0.35, shiver=0.0, alpha=1.0, squash=0.0, **self.persist)
        self.mouth = "smile"
        self.eyes = "open"
        self.hop = 0.0
        self.sweat = False

    def update(self, dt, t):
        k = 1 - math.exp(-SMOOTH * dt)
        for key, v in self.tgt.items():
            self.cur[key] += (v - self.cur[key]) * k
        if t >= self.next_blink:
            self.blink_t = t
            self.next_blink = t + self.rng.uniform(2.2, 4.5)

    def draw(self, ctx, t):
        c = self.cur
        if c["alpha"] < 0.02:
            return
        w = self.size / 2
        h = self.size * 0.52
        bob = math.sin(t * 2.6 + self.inner) * 0.02
        squash = bob + c["squash"]
        sx, sy = 1 + squash, 1 - squash
        shiver = math.sin(t * 60) * 5 * c["shiver"]
        hop = abs(math.sin(t * 9)) * 26 * self.hop
        cx = c["x"] + shiver
        cy = self.ground - h * sy - hop
        color = mix(self.base_color, self.twin_color, c["mix"])

        ctx.push_group()
        # shadow
        ctx.set_source_rgba(0.15, 0.05, 0.12, 0.18)
        ellipse(ctx, c["x"], self.ground + 6, w * 0.95, 14)
        ctx.fill()
        # feet
        for side in (-1, 1):
            ellipse(ctx, cx + side * w * 0.42, self.ground - 8 - hop, w * 0.24, 16)
            fill_stroke(ctx, mix(color, (0, 0, 0, 1), 0.12))

        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(math.radians(c["lean"]))
        ctx.scale(sx, sy)

        # arms behind the body edge
        self._arm(ctx, w, h, self.inner, c["arm_in"], color)
        self._arm(ctx, w, h, -self.inner, c["arm_out"], color)

        # body
        ctx.new_path()
        ctx.move_to(-w, 0.1 * h)
        ctx.curve_to(-w, -0.75 * h, -0.6 * w, -h, 0, -h)
        ctx.curve_to(0.6 * w, -h, w, -0.75 * h, w, 0.1 * h)
        ctx.curve_to(w, 0.75 * h, 0.7 * w, h, 0, h)
        ctx.curve_to(-0.7 * w, h, -w, 0.75 * h, -w, 0.1 * h)
        ctx.close_path()
        fill_stroke(ctx, color)
        # shine
        ctx.set_source_rgba(1, 1, 1, 0.35)
        ellipse(ctx, -0.45 * w, -0.6 * h, 0.16 * w, 0.1 * h)
        ctx.fill()

        self._accessory(ctx, w, h, color, c)
        self._face(ctx, w, h, t, c)
        ctx.restore()

        if self.sweat:
            ctx.set_source_rgba(0.55, 0.8, 1, 0.95)
            sx_ = cx + self.inner * -w * 0.75
            sy_ = cy - h * 0.6 + (t * 40 % 30)
            ctx.move_to(sx_, sy_ - 18)
            ctx.curve_to(sx_ + 12, sy_, sx_ + 10, sy_ + 14, sx_, sy_ + 14)
            ctx.curve_to(sx_ - 10, sy_ + 14, sx_ - 12, sy_, sx_, sy_ - 18)
            fill_stroke(ctx, (0.6, 0.85, 1, 1), width=4)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(c["alpha"])

    def hand_pos(self, side):
        """Screen position of a hand tip (side=+1 right, -1 left) for prop placement."""
        c = self.cur
        w = self.size / 2
        h = self.size * 0.52
        ang = math.radians(c["arm_in"] if side == self.inner else c["arm_out"])
        sx = c["x"] + side * 0.82 * w
        sy = self.ground - h + 0.15 * h
        length = 0.42 * w
        return sx + side * math.sin(ang) * length, sy + math.cos(ang) * length

    def _arm(self, ctx, w, h, side, angle, color):
        ctx.save()
        ctx.translate(side * 0.82 * w, 0.15 * h)
        ctx.rotate(-side * math.radians(angle))
        t = 0.22 * w
        rrect(ctx, -t / 2, -t / 2, t, 0.42 * w + t / 2, t / 2)
        fill_stroke(ctx, color)
        ctx.restore()

    def _accessory(self, ctx, w, h, color, c):
        acc = self.twin_accessory if c["mix"] > 0.5 else self.accessory
        if c["old"] > 0.05:
            # grey tuft
            ctx.save()
            for dx in (-0.22, 0.0, 0.22):
                ellipse(ctx, dx * w, -h * 0.98, 0.16 * w, 0.12 * w)
                fill_stroke(ctx, (0.88, 0.88, 0.9, c["old"]), width=5)
            ctx.restore()
        if acc == "sprout" and c["old"] < 0.6:
            ctx.set_source_rgba(*OUTLINE)
            ctx.set_line_width(6)
            ctx.move_to(0, -h)
            ctx.curve_to(0, -h - 25, 8, -h - 40, 6, -h - 50)
            ctx.stroke()
            for side in (-1, 1):
                ctx.save()
                ctx.translate(6, -h - 50)
                ctx.rotate(side * 0.6)
                ellipse(ctx, side * 22, 0, 24, 12)
                fill_stroke(ctx, hexc("7ccf6e"), width=5)
                ctx.restore()
        elif acc == "bow" and c["old"] < 0.6:
            bx, by = 0.42 * w, -0.86 * h
            for side in (-1, 1):
                ctx.move_to(bx, by)
                ctx.line_to(bx + side * 34, by - 20)
                ctx.line_to(bx + side * 34, by + 20)
                ctx.close_path()
                fill_stroke(ctx, hexc("ff6f9c"), width=5)
            ellipse(ctx, bx, by, 11, 11)
            fill_stroke(ctx, hexc("ff6f9c"), width=5)

    def _face(self, ctx, w, h, t, c):
        lx, ly = c["look_x"], c["look_y"]
        ex, ey = 0.3 * w, -0.18 * h
        ox, oy = lx * 0.13 * w, ly * 0.12 * h
        blink = 1.0
        if 0 <= t - self.blink_t < 0.14:
            blink = 0.12
        # blush
        ctx.set_source_rgba(1, 0.45, 0.55, 0.45 * c["blush"])
        for side in (-1, 1):
            ellipse(ctx, side * 0.56 * w + ox * 0.5, 0.05 * h + oy * 0.5, 0.15 * w, 0.08 * w)
            ctx.fill()
        for side in (-1, 1):
            x, y = side * ex + ox, ey + oy
            if self.eyes == "happy":
                ctx.set_source_rgba(*OUTLINE)
                ctx.set_line_width(7)
                ctx.arc(x, y + 6, 0.08 * w, math.pi * 1.1, math.pi * 1.9)
                ctx.stroke()
            elif self.eyes == "wide":
                ellipse(ctx, x, y, 0.1 * w, 0.13 * w * blink)
                fill_stroke(ctx, (1, 1, 1, 1), width=5)
                ellipse(ctx, x + lx * 4, y + ly * 4, 0.045 * w, 0.06 * w * blink)
                ctx.set_source_rgba(*OUTLINE)
                ctx.fill()
            else:
                ellipse(ctx, x, y, 0.075 * w, 0.1 * w * blink)
                ctx.set_source_rgba(*OUTLINE)
                ctx.fill()
                if blink > 0.5:
                    ctx.set_source_rgba(1, 1, 1, 0.95)
                    ellipse(ctx, x + 0.025 * w, y - 0.035 * w, 0.025 * w, 0.025 * w)
                    ctx.fill()
            if c["old"] > 0.05:  # round glasses
                ctx.set_source_rgba(*OUTLINE[:3], c["old"])
                ctx.set_line_width(5)
                ctx.new_sub_path()
                ctx.arc(x, y, 0.15 * w, 0, 2 * math.pi)
                ctx.stroke()
        if c["old"] > 0.05:
            ctx.set_source_rgba(*OUTLINE[:3], c["old"])
            ctx.move_to(-ex + ox + 0.15 * w, ey + oy)
            ctx.line_to(ex + ox - 0.15 * w, ey + oy)
            ctx.stroke()

        mx, my = ox * 0.8, 0.12 * h + oy * 0.6
        ctx.set_source_rgba(*OUTLINE)
        ctx.set_line_width(7)
        ctx.set_line_cap(1)
        m = self.mouth
        if m == "smile":
            ctx.arc(mx, my - 6, 0.12 * w, math.pi * 0.2, math.pi * 0.8)
            ctx.stroke()
        elif m == "grin":
            ctx.move_to(mx - 0.14 * w, my - 4)
            ctx.arc_negative(mx, my - 4, 0.14 * w, math.pi, 0)
            ctx.close_path()
            ctx.save()
            ctx.set_source_rgba(0.6, 0.15, 0.25, 1)
            ctx.fill_preserve()
            ctx.restore()
            ctx.stroke()
        elif m == "open":
            ellipse(ctx, mx, my + 2, 0.06 * w, 0.08 * w)
            fill_stroke(ctx, (0.6, 0.15, 0.25, 1), width=6)
        elif m == "sad":
            ctx.arc(mx, my + 14, 0.1 * w, math.pi * 1.2, math.pi * 1.8)
            ctx.stroke()
        elif m == "wobbly":
            ctx.move_to(mx - 0.12 * w, my)
            for i in range(1, 7):
                ctx.line_to(mx - 0.12 * w + i * 0.04 * w, my + (6 if i % 2 else -2))
            ctx.stroke()
        else:  # flat
            ctx.move_to(mx - 0.08 * w, my)
            ctx.line_to(mx + 0.08 * w, my)
            ctx.stroke()
        ctx.set_line_cap(0)
