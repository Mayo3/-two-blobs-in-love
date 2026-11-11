"""Speaks script lines with Chatterbox. Run by shorts/tts.py with the Python of the
environment Chatterbox is installed in (it needs other package versions than the rest):

    python chatterbox_lines.py job.json

job.json: {"lines": [...], "out": dir, "voices": [{"ref": voice clip, "exaggeration": 0.7, "cfg_weight": 0.4} per line]}
Writes 00.wav, 01.wav, ... into `out`. Imports nothing from the project.
"""
import json
import sys
import time
import zlib

TRIES = 3  # Chatterbox now and then garbles or trails off; such a take is far too long or too short


def plausible(seconds, words):
    """Speech runs at very roughly 0.2-0.5 seconds a word; allow wide margins around that."""
    return 0.1 * words + 0.2 <= seconds <= 0.8 * words + 1.5


def main():
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    import soundfile as sf
    import torch
    from chatterbox.tts import ChatterboxTTS

    t0 = time.time()
    model = ChatterboxTTS.from_pretrained(device="cpu")
    print(f"chatterbox: model ready in {time.time() - t0:.0f}s", flush=True)
    seed = zlib.crc32(" ".join(job["lines"]).encode("utf-8"))  # the same script always sounds the same
    copied = {}  # each voice is copied from its clip once, not once per line
    for n, line in enumerate(job["lines"]):
        voice = job["voices"][n]
        if voice["ref"] not in copied:
            model.prepare_conditionals(voice["ref"], exaggeration=voice["exaggeration"])
            copied[voice["ref"]] = model.conds
        model.conds = copied[voice["ref"]]
        for attempt in range(TRIES):
            torch.manual_seed(seed + n * 10 + attempt)
            wav = model.generate(line, exaggeration=voice["exaggeration"], cfg_weight=voice["cfg_weight"]).squeeze().numpy()
            seconds = len(wav) / model.sr
            if plausible(seconds, len(line.split())):
                break
            print(f"chatterbox: line {n + 1} take {attempt + 1} is {seconds:.1f}s for {len(line.split())} words, again", flush=True)
        else:
            sys.exit(f"chatterbox: no usable take of line {n + 1}")
        sf.write(f"{job['out']}/{n:02d}.wav", wav, model.sr)
        print(f"chatterbox: line {n + 1}/{len(job['lines'])} {seconds:.1f}s (at {time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
