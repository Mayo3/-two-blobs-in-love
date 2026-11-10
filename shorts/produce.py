"""Script → finished video. Shared by the sample renderer and the daily job."""
import os

from .captions import HOOK_Y, align, build_ass, hook_text, line_times, tokenize
from .cartoon.director import Animator, timed_beats
from .facts import FACT_BY_ID
from .render import audio_duration, render_cartoon, render_footage
from .style import check_script
from .tts import synthesize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
CHANNEL = "Two Blobs in Love"
VOICES = ["heart-nova"]  # Kokoro blend (see tts.BLENDS); one narrator so the channel always sounds the same


def produce(script, work, out_path, voice, style="cartoon"):
    """Render `script` to `out_path`. Returns the video duration in seconds."""
    fact = FACT_BY_ID[script["fact"]]
    problems = check_script(script, fact)
    if problems:
        raise ValueError(f"script failed checks: {problems}")
    os.makedirs(work, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    audio = "voice.mp3" if voice.startswith("en-") else "voice.wav"
    spoken = [line.replace("*", "") for line in script["lines"]]
    words = synthesize(spoken, voice, os.path.join(work, audio))
    duration = audio_duration(os.path.join(work, audio)) + 0.6
    tokens = align(tokenize(script["lines"]), words)
    lines = line_times(tokens, len(script["lines"]), duration)
    hook_end = lines[0][1]  # the hook stays up while line 1 is spoken
    with open(os.path.join(work, "captions.ass"), "w", encoding="utf-8") as f:
        f.write(build_ass(tokens, duration, script["palette"], fact["source"], CHANNEL, script["title"], hook_end=hook_end))
    if style == "footage":
        from .footage import pick_clips
        clips = pick_clips(script["footage"], seed=os.path.basename(out_path))
        render_footage(work, audio, "captions.ass", out_path, script["palette"], duration, FONTS, clips, lines)
    else:
        animator = Animator(script["scene"], timed_beats(script["beats"], lines), tokens, hook=(hook_end, HOOK_Y, hook_text(tokens)[1]))
        render_cartoon(work, audio, "captions.ass", out_path, script["palette"], duration, FONTS, animator)
    return duration
