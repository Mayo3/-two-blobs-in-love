"""The story channel's pilot. Usage:
  python make_tales.py voices             make the clip each character's Chatterbox voice is copied from (once)
  python make_tales.py sheet              draw the cast sheet to out/preview/tales/cast.png
  python make_tales.py [id ...] [--quick] render the pilot stories (all, or the ones named) to out/preview/tales/
                                          --quick: the fast Kokoro backup voices, to check the pictures
"""
import json
import os
import sys

from tales.cast import CAST, ROOT, VOICE_DIR

OUT = os.path.join(ROOT, "out", "preview", "tales")
# What each character reads for their voice clip: a few moods, so the copy has some range.
VOICE_TEXT = ("Okay, so listen to this. You will not believe what happened today. I walked in, and the whole "
              "place was empty. Empty! I asked who did it, and nobody said a word. Honestly? I almost laughed. "
              "Then I got a little bit angry. And then, I had a much better idea.")


def voices():
    import soundfile as sf
    from shorts.tts import _engine

    os.makedirs(VOICE_DIR, exist_ok=True)
    for name, spec in CAST.items():
        if os.path.exists(os.path.join(VOICE_DIR, f"{name}.wav")):
            continue
        audio, sr = _engine().create(VOICE_TEXT, voice=spec["kokoro"], speed=1.0, lang="en-us")
        path = os.path.join(VOICE_DIR, f"{name}.wav")
        sf.write(path, audio, sr)
        print(f"{path}  ({len(audio) / sr:.1f}s, copied from Kokoro {spec['kokoro']})")


def sheet():
    import cairo
    from shorts.cartoon.draw import hexc
    from tales.cast import Actor
    from tales.stage import label

    def write(text, size, x, y, color="2b2d42"):
        surf, _, _ = label(text, size, color)
        ctx.set_source_surface(surf, x, y)
        ctx.paint()

    w, h = 1080, 1620
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    ctx.set_source_rgba(*hexc("e9e4dc"))
    ctx.paint()
    write("The cast", 60, 50, 30)
    from tales.stage import FEELINGS

    class Still:  # the stage as a feeling sees it
        back, front, now = [], [], 1.3

    poses = {"mara": "sarcastic", "dex": "calm", "lulu": "laugh", "theo": "nervous", "ivy": "sip", "gus": "annoyed"}
    for i, (key, spec) in enumerate(CAST.items()):
        col, row = i % 3, i // 3
        x, ground = 190 + col * 350, 640 + row * 700
        a = Actor(key, x, ground, seed=i)
        a.reset(x)
        a.inner = 1 if col < 2 else -1
        a.tgt["look_x"] = 0.3 * a.inner
        st = Still()
        FEELINGS[poses[key]][0](st, a, 1.3, 0.5, a.inner)
        a.cur.update(a.tgt)
        st.front.clear()
        FEELINGS[poses[key]][0](st, a, 1.3, 0.5, a.inner)  # again, now that the hand is where the glass goes
        ctx.save()
        ctx.translate(x, ground)
        ctx.scale(0.74, 0.74)
        ctx.translate(-x, -ground)
        a.draw(ctx, 1.3)
        for f in st.front:
            f(ctx)
        ctx.restore()
        write(spec["label"], 40, x - 130, ground + 30, spec["tag"])
        words, line, y = spec["about"].split(), "", ground + 90
        for word in words + [None]:
            if word is None or len(f"{line} {word}") > 24:
                write(line.strip(), 19, x - 130, y)
                line, y = "", y + 28
            if word:
                line = f"{line} {word}"
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "cast.png")
    surf.write_to_png(path)
    print(path)


def render(ids, quick):
    from tales.produce import produce

    stories = json.load(open(os.path.join(ROOT, "tales", "stories.json"), encoding="utf-8"))
    for s in stories:
        if ids and s["id"] not in ids:
            continue
        name = f"{s['id']}{' (quick voices)' if quick else ''}"
        out = os.path.join(OUT, f"{name}.mp4")
        seconds = produce(s, os.path.join(ROOT, "build", f"tales-{s['id']}{'-quick' if quick else ''}"), out,
                          "cast-kokoro" if quick else "cast")
        print(f"{out}  ({seconds:.1f}s)", flush=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args[:1] == ["voices"]:
        voices()
    elif args[:1] == ["sheet"]:
        sheet()
    else:
        render(args, "--quick" in sys.argv)
