"""The daily job: pick a fact, write a script, render the video, record it in history.

Usage: python -m shorts.daily [--date YYYY-MM-DD] [--script file.json]
  --script  render a ready-made script instead of asking the LLM (for testing)
In GitHub Actions it also writes step outputs (video, meta, date) for the publish steps.
"""
import argparse
import datetime as dt
import json
import os
import sys

from .facts import FACTS, FACT_BY_ID
from .produce import ROOT, VOICES, produce

HISTORY = os.path.join(ROOT, "state", "history.json")
REUSE_AFTER_DAYS = 20  # a fact can come back, in a format not used for it yet, after this long
RECENT_SCENES = 2  # a scene is not used again until this many videos later
HASHTAGS = "#couples #relationships #lovefacts #psychologyfacts #couplegoals"


def load_history():
    if os.path.exists(HISTORY):
        return json.load(open(HISTORY, encoding="utf-8"))
    return []


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        f.write("\n")


def pick(history, today):
    """Next fact and format: unused facts first, then the longest-unused ones."""
    from .writer import FORMATS

    last = {}
    for h in history:
        last[h["fact"]] = max(last.get(h["fact"], ""), h["date"])
    cutoff = (today - dt.timedelta(days=REUSE_AFTER_DAYS)).isoformat()
    facts = [f for f in FACTS if f["verified"]]
    fresh = [f for f in facts if f["id"] not in last]
    stale = sorted((f for f in facts if f["id"] in last and last[f["id"]] <= cutoff), key=lambda f: last[f["id"]])
    if not fresh and not stale:
        raise SystemExit("Fact bank exhausted: every fact was used in the last %d days. Add facts to shorts/facts.py." % REUSE_AFTER_DAYS)
    fact = (fresh or stale)[0]

    used_for_fact = {h["format"] for h in history if h["fact"] == fact["id"]}
    if fact["topic"] == "myth" and "myth-vs-fact" not in used_for_fact:
        return fact, "myth-vs-fact"
    options = [f for f in FORMATS if f != "myth-vs-fact" and f not in used_for_fact] or [f for f in FORMATS if f != "myth-vs-fact"]
    recent = [h["format"] for h in history[-len(FORMATS):]]
    options.sort(key=lambda f: recent.count(f))  # rotate formats across days
    return fact, options[0]


def scene_options(history):
    """Scenes the writer may choose from: any not used in the last RECENT_SCENES videos."""
    from .cartoon.scenes import Scene

    recent = {h.get("scene") for h in history[-RECENT_SCENES:]}
    return [k for k in Scene.kinds if k not in recent] or list(Scene.kinds)


def tiktok_caption(script, fact):
    return f"{script['caption']} (Source: {fact['source']}) {HASHTAGS}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--script")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.date)
    history = load_history()

    if args.script:
        script = json.load(open(args.script, encoding="utf-8"))
        fact = FACT_BY_ID[script["fact"]]
        script.setdefault("format", "story")
        script.setdefault("caption", script["title"])
    else:
        from .writer import write_script
        fact, fmt = pick(history, today)
        print(f"fact: {fact['id']}  format: {fmt}")
        scenes = scene_options(history)
        print(f"scenes: {', '.join(scenes)}")
        script = write_script(fact, fmt, scenes)

    voice = VOICES[len(history) % len(VOICES)]
    name = f"{today.isoformat()}-{fact['id']}"
    out_dir = os.path.join(ROOT, "out", today.isoformat())
    video = os.path.join(out_dir, f"{name}.mp4")
    duration = produce(script, os.path.join(ROOT, "build", name), video, voice)

    meta = {
        "date": today.isoformat(), "fact": fact["id"], "format": script["format"], "scene": script["scene"], "voice": voice,
        "title": script["title"], "caption": tiktok_caption(script, fact), "source": fact["source"],
        "video": video, "duration": round(duration, 1), "script": script,
    }
    meta_path = os.path.join(out_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    history.append({k: meta[k] for k in ("date", "fact", "format", "scene", "voice", "title")})
    save_history(history)
    print(f"{video}  ({duration:.1f}s)\n{meta['caption']}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"video={video}\nmeta={meta_path}\ndate={today.isoformat()}\n")


if __name__ == "__main__":
    sys.exit(main())
