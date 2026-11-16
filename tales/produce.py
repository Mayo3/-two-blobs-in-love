"""Story → finished video, with the voices, captions and renderer of Two Blobs in Love."""
import os

from shorts.captions import HOOK_Y, PALETTES, align, build_ass, hook_text, line_times, tokenize
from shorts.render import audio_duration, render_cartoon
from shorts import tts
from shorts.tts import SOUNDS, synthesize

from .cast import CAST, ROOT, SPEAKER_COLORS
from .stage import FONT_NAME, Stage, hit_time, plan

FONTS = os.path.join(ROOT, "fonts")
CHANNEL = "Did I Go Too Far?"  # working name, shown at the top of every video
MAX_CLOUD_WORDS = 12  # the hook and the closing question are shown whole in the cloud
VOICE_TEMPERATURE = 0.95  # these stories are acted, not read: let the voices swing more than the blobs' do
MIN_WORDS, MAX_WORDS = 80, 150  # roughly 35 to 60 seconds


def check(story):
    """Problems that would make a story unusable. An empty list means it can be rendered."""
    problems = []
    lines = story.get("lines", [])
    texts = [line["text"].replace("*", "") for line in lines]
    if len(lines) < 6:
        return ["a story needs at least 6 lines"]
    try:
        staged = plan(lines, story.get("scene"))
    except ValueError as e:
        return [str(e)]
    for line in lines:
        if line["who"] not in CAST:
            problems.append(f"unknown character '{line['who']}'")
        if line.get("sound") and line["sound"] not in SOUNDS:
            problems.append(f"unknown sound '{line['sound']}'")
    if max(len(p["on"]) for p in staged) > 4:
        problems.append("more than 4 characters on stage at once")
    if len({n for p in staged for n in p["on"]}) < 3:
        problems.append("a story needs at least 3 characters")
    words = sum(len(t.split()) for t in texts)
    if not MIN_WORDS <= words <= MAX_WORDS:
        problems.append(f"length {words} words (want {MIN_WORDS}-{MAX_WORDS})")
    for i, name in ((0, "hook"), (-1, "closing question")):
        if len(texts[i].split()) > MAX_CLOUD_WORDS:
            problems.append(f"{name} longer than {MAX_CLOUD_WORDS} words")
        if lines[i].get("to") != "viewer":
            problems.append(f"the {name} must be said to the viewer")
    if not texts[-1].rstrip().endswith("?"):
        problems.append("the last line is not a question for the viewer")
    if story.get("palette") not in PALETTES:
        problems.append(f"unknown palette '{story.get('palette')}'")
    return problems


def thuds(path, at):
    """Mix the sound of a blow into the voice track at each of the times `at` (seconds)."""
    if not at:
        return
    import numpy as np
    import soundfile as sf

    audio, sr = sf.read(path, dtype="float32")
    t = np.arange(int(sr * 0.5)) / sr
    rng = np.random.default_rng(7)
    hit = (0.9 * np.sin(2 * np.pi * 120 * t) * np.exp(-t * 26)  # the thud
           + 0.5 * rng.standard_normal(len(t)) * np.exp(-t * 70)  # the smack
           + 0.16 * (np.sin(2 * np.pi * 640 * t) + 0.6 * np.sin(2 * np.pi * 1510 * t)) * np.exp(-t * 9))  # it rings a little
    hit = (hit * 0.8 * max(0.2, float(np.abs(audio).max()))).astype("float32")
    for when in at:
        a = int(when * sr)
        n = min(len(hit), len(audio) - a)
        if n > 0:
            audio[a:a + n] += hit[:n] if audio.ndim == 1 else hit[:n, None]
    sf.write(path, np.clip(audio, -1, 1), sr)


def produce(story, work, out_path, voice="cast"):
    """Render `story` to `out_path`. voice: "cast" (Chatterbox) or "cast-kokoro" (quick backup voices).
    Returns the video duration in seconds."""
    problems = check(story)
    if problems:
        raise ValueError(f"story failed checks: {problems}")
    os.makedirs(work, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    lines = story["lines"]
    texts = [line["text"] for line in lines]
    speakers = [line["who"] for line in lines]
    calm, tts.TEMPERATURE = tts.TEMPERATURE, VOICE_TEMPERATURE
    try:
        words = synthesize([t.replace("*", "") for t in texts], voice, os.path.join(work, "voice.wav"),
                           speakers=speakers, sounds=[line.get("sound") for line in lines])
    finally:
        tts.TEMPERATURE = calm
    duration = audio_duration(os.path.join(work, "voice.wav")) + 0.6
    tokens = align(tokenize(texts), words)
    for t in tokens:
        t["who"] = speakers[t["line"]]
    times = line_times(tokens, len(lines), duration)
    thuds(os.path.join(work, "voice.wav"), [hit_time(*times[i]) for i, line in enumerate(lines) if line.get("hit")])
    hook_end, last = times[0][1], len(lines) - 1
    outro_start = times[last][0]
    with open(os.path.join(work, "captions.ass"), "w", encoding="utf-8") as f:
        f.write(build_ass(tokens, duration, story["palette"], CHANNEL, story["title"], hook_end=hook_end,
                          outro_start=outro_start, cast=True, speaker_colors=SPEAKER_COLORS, font=FONT_NAME))
    clouds = [{"start": 0.0, "end": hook_end, "y": HOOK_Y, "rows": hook_text(tokens)[1], "pop": False, "fade": True},
              {"start": outro_start, "end": duration + 1, "y": HOOK_Y, "rows": hook_text(tokens, last)[1], "pop": True, "fade": False}]
    stage = Stage(story.get("scene"), lines, times, tokens, clouds=clouds, roles=story.get("roles"))
    render_cartoon(work, "voice.wav", "captions.ass", out_path, story["palette"], duration, FONTS, stage)
    return duration
