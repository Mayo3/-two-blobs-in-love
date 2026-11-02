"""Real stock footage from Pixabay (free API, commercial use allowed, no attribution needed).

Each script line has a search query; we pick a fitting clip that isn't already used
in the same video and cache downloads so repeated renders don't refetch.
"""
import os
import random

import requests

API = "https://pixabay.com/api/videos/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "build", "cache", "pixabay")


def api_key():
    key = os.environ.get("PIXABAY_API_KEY")
    if key:
        return key
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            name, _, value = line.strip().partition("=")
            if name == "PIXABAY_API_KEY":
                return value.strip()
    raise SystemExit("PIXABAY_API_KEY missing (set it in .env or the environment)")


def search(query, per_page=20):
    r = requests.get(API, params={"key": api_key(), "q": query, "per_page": per_page, "safesearch": "true", "video_type": "film"}, timeout=30)
    r.raise_for_status()
    return r.json()["hits"]


def _rendition(hit):
    """Smallest rendition that is still at least 1080 px tall (cropping to vertical needs height)."""
    vids = sorted(hit["videos"].values(), key=lambda v: v.get("height") or 0)
    for v in vids:
        if v.get("url") and (v.get("height") or 0) >= 1080:
            return v
    return vids[-1]


def pick_clips(queries, seed, min_duration=3):
    """One clip per query, no repeats. Returns local file paths."""
    rng = random.Random(seed)
    used = set()
    paths = []
    for q in queries:
        hits = [h for h in search(q) if h["duration"] >= min_duration and h["id"] not in used]
        if not hits:
            hits = [h for h in search(q.split()[-1]) if h["id"] not in used]
        if not hits:
            raise RuntimeError(f"no footage found for '{q}'")
        hit = rng.choice(hits[:6])  # top results fit best; a little randomness keeps videos fresh
        used.add(hit["id"])
        paths.append(download(hit))
    return paths


def download(hit):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{hit['id']}.mp4")
    if not os.path.exists(path):
        with requests.get(_rendition(hit)["url"], stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(path + ".part", "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        os.replace(path + ".part", path)
    return path
