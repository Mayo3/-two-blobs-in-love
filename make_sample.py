"""Render the hand-written sample scripts to out/. Usage: python make_sample.py [index] [--footage]"""
import json
import os
import sys

from shorts.produce import ROOT, produce

if __name__ == "__main__":
    scripts = json.load(open(os.path.join(ROOT, "samples", "scripts.json"), encoding="utf-8"))
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    style = "footage" if "--footage" in sys.argv else "cartoon"
    picks = [int(args[0])] if args else range(len(scripts))
    for i in picks:
        s = scripts[i]
        name = f"sample-{i + 1}-{s['fact']}{'-footage' if style == 'footage' else ''}"
        out = os.path.join(ROOT, "out", f"{name}.mp4")
        duration = produce(s, os.path.join(ROOT, "build", name), out, s["voice"], style)
        print(f"{out}  ({duration:.1f}s)")
