"""Phone push via ntfy: the finished video's download link, a ready-to-paste caption and source comment.

Usage: python -m shorts.notify path/to/meta.json VIDEO_URL
Needs NTFY_TOPIC. Uses ntfy's JSON API so titles with any characters work.
"""
import json
import os
import sys

import requests


def main():
    meta = json.load(open(sys.argv[1], encoding="utf-8"))
    video_url = sys.argv[2]
    topic = os.environ["NTFY_TOPIC"]
    run_url = ""
    if os.environ.get("GITHUB_RUN_ID"):
        run_url = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    actions = [{"action": "view", "label": "Download video", "url": video_url}]
    if run_url:
        actions.append({"action": "view", "label": "Details", "url": run_url})
    # what shorts.crosspost already put up on the other platforms
    posted = meta.get("posted", {})
    elsewhere = " · ".join(f"{name} ✓" if res.get("id") else f"{name} ✗ ({res.get('error', '')[:80]})"
                           for name, res in posted.items())
    for name, res in posted.items():
        if res.get("url") and len(actions) < 3:  # ntfy shows at most three buttons
            actions.append({"action": "view", "label": f"Open on {name}", "url": res["url"]})
    r = requests.post("https://ntfy.sh/", json={
        "topic": topic,
        "title": f"🎬 New TikTok ready: {meta['title']}",
        "message": f"{meta['caption']}\n\nPin as first comment:\n{meta['comment']}\n\n"
                   + (f"Already posted: {elsewhere}\n\n" if elsewhere else "")
                   + f"({meta['duration']}s · voice: {meta['voice']} · long-press to copy)",
        "tags": ["two_hearts"],
        "click": video_url,
        "actions": actions,
    }, timeout=30)
    r.raise_for_status()
    print("notified")


if __name__ == "__main__":
    main()
