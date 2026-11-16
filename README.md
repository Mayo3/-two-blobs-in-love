# Two Blobs in Love 💕

A free, automated TikTok channel: one short video a day with a science-backed fact about couples,
told as a little conversation between two cartoon blobs, Pip (pink, sprout, guesses first) and Bo (purple, bow,
knows the answer), who act out every line.

Every morning GitHub Actions:
1. picks a fact from the curated bank (`shorts/facts.py`), rotating facts and formats so nothing repeats,
2. writes the script with a free model (Google Gemini's free tier) — scripts must pass the anti-slop checks in `shorts/style.py` or get rewritten,
3. renders the video (Chatterbox voice, Cairo cartoon, ffmpeg),
4. attaches it to a GitHub release and sends your phone a push with a download link and a ready-to-paste caption.

You post it on TikTok yourself (about 30 seconds; add a trending sound). That's also your quality check.

Everything is free: GitHub Actions, Gemini free tier, Chatterbox and Kokoro (open-source voices), ntfy.

Pip and Bo speak with Chatterbox Turbo, which can chuckle, laugh, gasp and sigh, in voices copied from `voices/pip.wav` and
`voices/sarah.wav` (both synthetic voices). It is a 4 GB model that needs about 5-15 minutes a video on GitHub's
machines; if it can't run, two Kokoro voices speak instead and the phone notification says `cast-kokoro`.

## Setup

1. **Create the repo** on GitHub under your personal account (public is recommended — public repos get unlimited Actions minutes).
2. **Phone notifications:** install the ntfy app and subscribe to a hard-to-guess topic, e.g. `twoblobs-7f3k9q`.
   In the repo: *Settings → Secrets and variables → Actions → New repository secret* → `NTFY_TOPIC` = that topic.
3. **AI writer:** get a free Google Gemini key at https://aistudio.google.com/apikey (no card needed) and add it
   as repository secret `GEMINI_API_KEY`.
4. **Run it once by hand:** *Actions → daily-video → Run workflow*. After ~5 minutes your phone should buzz.

## Posting to YouTube, Instagram and Facebook too (optional)

After the release, the job also posts the video as a YouTube Short, an Instagram Reel and a Facebook Reel
(`shorts/crosspost.py`), with the same caption plus the source line. Each platform runs only once its secrets are
set, so switch them on one at a time; a failure is shown in the phone notification and never stops the run.
TikTok stays manual: its API only posts private videos until the app passes TikTok's audit.

**YouTube** (about 10 minutes, once):
1. https://console.cloud.google.com → new project → *APIs & Services → Library* → enable **YouTube Data API v3**.
2. *OAuth consent screen*: External, add yourself as a test user, then **Publish app** (in "Testing" mode the
   login expires after 7 days). Google shows an "unverified app" warning on login; that's fine for your own channel.
3. *Credentials → Create credentials → OAuth client ID → Desktop app*.
4. Locally: `python -m shorts.crosspost login-youtube`, paste the client ID and secret, log in with the channel's
   account. Add the three printed values as secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
5. Check the first upload: if YouTube marks it private, the Google project needs YouTube's API audit
   (form at https://support.google.com/youtube/contact/yt_api_form); the notification says so.

**Instagram + Facebook** (one Meta setup covers both):
1. A Facebook Page for the channel, and an Instagram account switched to *Professional* and linked to that Page.
2. https://developers.facebook.com → *Create app* (type Business). Your own accounts work without app review
   while you are the app's admin.
3. *Tools → Graph API Explorer*: pick the app, add permissions `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`, `business_management`, and *Generate token*.
4. Locally: `python -m shorts.crosspost login-meta`, paste the app ID, app secret and that token, pick the Page.
   Add the printed `META_PAGE_ID`, `META_PAGE_TOKEN` (it does not expire) and `IG_USER_ID` as secrets.

Test on an existing video without waiting for the morning:
`python -m shorts.crosspost out/<date>/meta.json --only youtube --youtube-privacy unlisted`
(it skips platforms where that video is already posted, so a rerun never double-posts).

## Running locally

```sh
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows
# voice model (once): download kokoro-v1.0.onnx and voices-v1.0.bin from
# https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 into models/
python make_sample.py                                      # render the 3 hand-written samples to out/ (quick Kokoro voices)
# Chatterbox voice (optional, 4.6 GB): python -m venv voice-lab/.venv-chatterbox, then in it
#   pip install chatterbox-tts==0.1.7 "setuptools<81" soundfile   — without it the daily job uses Kokoro
python -m shorts.daily --script build/test-script.json     # render a ready-made script like the daily job
GEMINI_API_KEY=... python -m shorts.daily                  # full run with the AI writer
```

## The story channel (pilot)

`tales/` is a second channel in the making, for viewers in their twenties: one-minute betrayal and revenge
stories ("I read his texts as my wedding vows") that end on a question for the comments. A troupe of six adults
(Mara, Dex, Lulu, Theo, Ivy, Gus) plays a different part in each story. It shares the voice, caption and render
code with the blobs but has its own look: web-comic people with adult proportions (`tales/cast.py`), flat places
under a cool film grade (`tales/sets.py`) and its own typeface (Poppins). Each story is a little film: a line can
cut to another place, to a memory with a time stamp, to a close-up, or hold up a phone with the messages somebody
was not meant to see; `tales/stage.py` lists what a line may say. The three pilot stories are hand-written in
`tales/stories.json`; there is no daily job for it yet.

```sh
python make_tales.py sheet            # the cast, to out/preview/tales/cast.png
python make_tales.py --quick          # all pilot stories with the quick Kokoro voices
python make_tales.py vows             # one story with the Chatterbox voices
```

## Adding facts

The bank holds ~3 months of videos (each fact returns in a new format after 20 days). To grow it,
add entries to `shorts/facts.py`: one finding per entry, from a real study, with the citation, and
`verified: True` only after checking the numbers against the source. The job tells you when the bank runs dry.

## Layout

- `shorts/facts.py`, `shorts/style.py` — what may be said, and how
- `shorts/writer.py`, `shorts/llm.py` — script writing with a free model
- `shorts/tts.py`, `shorts/chatterbox_lines.py`, `voices/` — the narrator (Chatterbox, Kokoro as backup) + word timings for captions
- `shorts/cartoon/` — characters, scenes, props and the action vocabulary the scripts use
- `shorts/captions.py`, `shorts/render.py`, `shorts/produce.py` — captions and final render
- `shorts/daily.py`, `shorts/notify.py`, `.github/workflows/daily.yml` — the daily job
- `shorts/footage.py` — optional Pixabay stock-footage style (not used by the daily job)
