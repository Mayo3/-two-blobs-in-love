# Two Blobs in Love 💕

A free, automated TikTok channel: one short video a day with a science-backed fact about couples,
narrated over a cartoon of two blob characters who act out every line.

Every morning GitHub Actions:
1. picks a fact from the curated bank (`shorts/facts.py`), rotating facts and formats so nothing repeats,
2. writes the script with a free model (Google Gemini's free tier) — scripts must pass the anti-slop checks in `shorts/style.py` or get rewritten,
3. renders the video (Kokoro voice, Cairo cartoon, ffmpeg),
4. attaches it to a GitHub release and sends your phone a push with a download link and a ready-to-paste caption.

You post it on TikTok yourself (about 30 seconds; add a trending sound). That's also your quality check.

Everything is free: GitHub Actions, Gemini free tier, Kokoro (open-source voice), ntfy.

## Setup

1. **Create the repo** on GitHub under your personal account (public is recommended — public repos get unlimited Actions minutes).
2. **Phone notifications:** install the ntfy app and subscribe to a hard-to-guess topic, e.g. `twoblobs-7f3k9q`.
   In the repo: *Settings → Secrets and variables → Actions → New repository secret* → `NTFY_TOPIC` = that topic.
3. **AI writer:** get a free Google Gemini key at https://aistudio.google.com/apikey (no card needed) and add it
   as repository secret `GEMINI_API_KEY`.
4. **Run it once by hand:** *Actions → daily-video → Run workflow*. After ~5 minutes your phone should buzz.

## Running locally

```sh
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows
# voice model (once): download kokoro-v1.0.onnx and voices-v1.0.bin from
# https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 into models/
python make_sample.py                                      # render the 3 hand-written samples to out/
python -m shorts.daily --script build/test-script.json     # render a ready-made script like the daily job
GEMINI_API_KEY=... python -m shorts.daily                  # full run with the AI writer
```

## Adding facts

The bank holds ~3 months of videos (each fact returns in a new format after 20 days). To grow it,
add entries to `shorts/facts.py`: one finding per entry, from a real study, with the citation, and
`verified: True` only after checking the numbers against the source. The job tells you when the bank runs dry.

## Layout

- `shorts/facts.py`, `shorts/style.py` — what may be said, and how
- `shorts/writer.py`, `shorts/llm.py` — script writing with a free model
- `shorts/tts.py` — Kokoro voice + word timings for captions
- `shorts/cartoon/` — characters, scenes, props and the action vocabulary the scripts use
- `shorts/captions.py`, `shorts/render.py`, `shorts/produce.py` — captions and final render
- `shorts/daily.py`, `shorts/notify.py`, `.github/workflows/daily.yml` — the daily job
- `shorts/footage.py` — optional Pixabay stock-footage style (not used by the daily job)
