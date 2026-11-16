"""Render the TikTok profile picture: the two blobs cuddled up, framed for TikTok's circle crop."""
import math
from pathlib import Path

import cairo

from shorts.cartoon.characters import Blob
from shorts.cartoon.draw import OUTLINE, ellipse, fill_stroke, heart, hexc

S = 1080
OUT = Path("out/avatar.png")


def main():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    ctx = cairo.Context(surf)

    g = cairo.RadialGradient(S / 2, S * 0.45, 60, S / 2, S / 2, S * 0.72)
    g.add_color_stop_rgba(0, *hexc("ffd6dc"))
    g.add_color_stop_rgba(1, *hexc("f08aa6"))
    ctx.set_source(g)
    ctx.paint()
    # a few soft background hearts
    for x, y, s, a in ((190, 230, 34, 0.35), (880, 260, 26, 0.3), (150, 640, 22, 0.25), (930, 600, 30, 0.3)):
        heart(ctx, x, y, s)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.fill()

    ground = 830
    a = Blob("A", "ff9a8b", "sprout", 385, ground, 400, +1, seed=1)
    b = Blob("B", "b9a3f5", "bow", 705, ground, 380, -1, seed=2)
    a.persist["old"] = b.persist["old"] = 0.0
    for blob, home in ((a, 385), (b, 705)):
        blob.reset(home)
        blob.tgt.update(lean=6 * blob.inner, blush=1.0, arm_in=70, arm_out=20)
        blob.cur.update(blob.tgt)
        blob.eyes = "happy"
        blob.mouth = "grin"
        blob.blink_t = -10
    a.draw(ctx, 0.0)
    b.draw(ctx, 0.0)

    # the heart they share, above and between them
    hx, hy = 545, 300
    ctx.set_source_rgba(1, 1, 1, 0.6)
    heart(ctx, hx, hy, 96)
    ctx.fill()
    heart(ctx, hx, hy, 82)
    fill_stroke(ctx, hexc("ff4f86"), width=8)
    ctx.set_source_rgba(1, 1, 1, 0.55)
    ellipse(ctx, hx - 34, hy - 30, 13, 9)
    ctx.fill()

    OUT.parent.mkdir(exist_ok=True)
    surf.write_to_png(str(OUT))

    # circle-crop preview, as TikTok shows it
    prev = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    pc = cairo.Context(prev)
    pc.arc(S / 2, S / 2, S / 2, 0, 2 * math.pi)
    pc.clip()
    pc.set_source_surface(surf, 0, 0)
    pc.paint()
    prev.write_to_png(str(OUT.with_name("avatar-circle-preview.png")))
    print(OUT)


if __name__ == "__main__":
    main()
