"""Speaks script lines with Chatterbox Turbo. Run by shorts/tts.py with the Python of the
environment Chatterbox is installed in (it needs other package versions than the rest):

    python chatterbox_lines.py job.json

job.json: {"lines": [...], "refs": [voice clip per line], "out": dir}
A line may start with a sound in square brackets that Turbo acts out: "[chuckle] That was a bid."
Writes 00.wav, 01.wav, ... into `out`. Imports nothing from the project.
"""
import json
import re
import sys
import time
import zlib

TRIES = 3  # Chatterbox now and then garbles or trails off; such a take is far too long or too short
SOUND = re.compile(r"\[[a-z ]+\]")


def plausible(seconds, line):
    """Speech runs at very roughly 0.2-0.5 seconds a word; allow wide margins around that,
    and up to a few seconds more for a laugh or a sigh."""
    words, sounds = len(SOUND.sub("", line).split()), len(SOUND.findall(line))
    return 0.1 * words + 0.2 <= seconds <= 0.8 * words + 1.5 + 2.5 * sounds


def main():
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    import soundfile as sf
    import torch
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    t0 = time.time()
    model = ChatterboxTurboTTS.from_pretrained(device="cpu")
    # 0.1.7: its loudness step hands back 64-bit audio, which the next step rejects
    level = model.norm_loudness
    model.norm_loudness = lambda wav, sr, target_lufs=-27: level(wav, sr, target_lufs).astype("float32")
    print(f"chatterbox: model ready in {time.time() - t0:.0f}s", flush=True)
    seed = zlib.crc32(" ".join(job["lines"]).encode("utf-8"))  # the same script always sounds the same
    copied = {}  # each voice is copied from its clip once, not once per line
    for n, line in enumerate(job["lines"]):
        ref = job["refs"][n]
        if ref not in copied:
            model.prepare_conditionals(ref)
            copied[ref] = model.conds
        model.conds = copied[ref]
        for attempt in range(TRIES):
            torch.manual_seed(seed + n * 10 + attempt)
            wav = model.generate(line).squeeze().numpy()
            seconds = len(wav) / model.sr
            if plausible(seconds, line):
                break
            print(f"chatterbox: line {n + 1} take {attempt + 1} is {seconds:.1f}s for '{line}', again", flush=True)
        else:
            sys.exit(f"chatterbox: no usable take of line {n + 1}")
        sf.write(f"{job['out']}/{n:02d}.wav", wav, model.sr)
        print(f"chatterbox: line {n + 1}/{len(job['lines'])} {seconds:.1f}s (at {time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
