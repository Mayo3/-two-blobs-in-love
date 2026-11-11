"""Text-to-speech with per-word timings for captions.

The narrator is Chatterbox (open-source, reads with feeling) speaking in a voice copied
from a short clip in voices/. It is big and slow, so it runs in its own Python environment
(see shorts/chatterbox_lines.py); if it is missing or fails, Kokoro (small, fast, calmer)
reads the script instead, so there is always a video. Neither gives word timings, so we
synthesize line by line, find the pauses in each line's audio, match them to its
punctuation, and spread words between pauses by phoneme count.
Edge TTS (voice names starting with "en-") is kept as a further fallback.
"""
import asyncio
import json
import os
import random
import re
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, "models", "kokoro-v1.0.onnx")
VOICES_BIN = os.path.join(ROOT, "models", "voices-v1.0.bin")
LINE_PAUSE = {".": 0.42, "?": 0.48, "!": 0.42, "…": 0.5}  # silence after a line, by its last char
DEFAULT_LINE_PAUSE = 0.3
HOOK_PAUSE = 0.28  # after line 1: viewers decide to stay or swipe right here, so the answer starts at once
LEAD_IN = 0.15  # just enough silence that players don't clip the first word
SPEED = 0.92  # a little slower than default reads calmer and more natural
# a person never reads every line at the same pace or pauses the same length; small random
# changes per line make the narration sound much less robotic (seeded by the script, so repeatable)
PACE_JITTER = (-0.04, 0.05)  # added to SPEED per line
PAUSE_JITTER = (0.75, 1.35)  # multiplies the pause after each line
# custom voices: weighted mixes of Kokoro's built-in voices
BLENDS = {"heart-nova": {"af_heart": 0.6, "af_nova": 0.4}}
# Chatterbox voices: the clip whose speaker is copied, how much feeling (0.5 is neutral), and how
# closely to follow the clip's own pace (lower lets the feeling lead)
CHATTERBOX = {"sarah-warm": {"ref": os.path.join(ROOT, "voices", "sarah.wav"), "exaggeration": 0.7, "cfg_weight": 0.4}}
CHATTERBOX_TIMEOUT = 25 * 60  # seconds; on a 4-core machine a video's speech takes roughly 5-15 minutes
BACKUP_VOICE = "heart-nova"  # Kokoro, when Chatterbox can't be used
LAST_VOICE = None  # the voice the last synthesize() call really used

_kokoro = None


def _engine():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(MODEL, VOICES_BIN)
    return _kokoro


def synthesize(lines, voice, out_path, speed=SPEED):
    """Speak script lines (plain text, no *markers*) into `out_path` (.wav for Kokoro, .mp3 for Edge).
    Returns [{text, start, end}] per word, in seconds."""
    global LAST_VOICE
    LAST_VOICE = voice
    if voice.startswith("en-"):
        return _edge(" ".join(lines), voice, out_path)
    if voice in CHATTERBOX:
        try:
            return _join_lines(lines, out_path, _chatterbox_audio(lines, voice))
        except Exception as e:  # never lose the day's video over the voice
            print(f"Chatterbox voice '{voice}' failed ({e}); narrating with {BACKUP_VOICE} instead")
            LAST_VOICE = voice = BACKUP_VOICE
    return _join_lines(lines, out_path, _kokoro_audio(lines, voice, speed))


# ---------- Kokoro ----------

def _speech_spans(audio, sr, min_gap=0.11, thresh_ratio=0.06):
    """(start, end) seconds of speech, split at silent gaps of at least `min_gap`."""
    hop = int(sr * 0.01)
    frames = len(audio) // hop
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2)) for i in range(frames)])
    loud = rms > rms.max() * thresh_ratio
    spans, start, silent = [], None, 0
    for i, on in enumerate(loud):
        if on:
            if start is None:
                start = i
            silent = 0
        elif start is not None:
            silent += 1
            if silent * 0.01 >= min_gap:
                spans.append((start * 0.01, (i - silent + 1) * 0.01))
                start, silent = None, 0
    if start is not None:
        spans.append((start * 0.01, (frames - silent) * 0.01))
    return spans


def _phoneme_weight(word):
    clean = re.sub(r"[^\w%']", "", word)
    if not clean:
        return 0
    try:
        return max(1, len(_engine().tokenizer.phonemize(clean, "en-us").replace(" ", "")))
    except Exception:
        return max(1, len(clean))


def _at(spans, frac):
    """Time at fraction `frac` of the speaking time covered by `spans` (silences skipped)."""
    total = sum(e - s for s, e in spans)
    left = frac * total
    for s, e in spans:
        if left <= e - s:
            return s + left
        left -= e - s
    return spans[-1][1]


def _time_line(words, spans):
    """Assign word times inside one line given its speech spans."""
    if not spans:
        spans = [(0.0, 0.5)]
    # Phrases end at punctuation; the longest pauses in the audio are the phrase breaks.
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[,.;:!?…]$", w):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    if len(spans) >= len(phrases):
        gaps = sorted(range(len(spans) - 1), key=lambda i: spans[i + 1][0] - spans[i][1], reverse=True)
        cuts = sorted(gaps[: len(phrases) - 1])
        groups, start = [], 0
        for c in cuts + [len(spans) - 1]:
            groups.append(spans[start:c + 1])
            start = c + 1
    else:
        phrases, groups = [words], [spans]
    out = []
    for phrase, group in zip(phrases, groups):
        weights = [_phoneme_weight(w) or 1 for w in phrase]
        total = sum(weights)
        acc = 0
        for w, wt in zip(phrase, weights):
            out.append({"text": w, "start": _at(group, acc / total), "end": _at(group, (acc + wt) / total)})
            acc += wt
    return out


def _kokoro_audio(lines, voice, speed):
    """[(audio, sample rate)] per line."""
    k = _engine()
    style = sum(w * k.get_voice_style(n) for n, w in BLENDS[voice].items()) if voice in BLENDS else voice
    rng = random.Random("pace " + " ".join(lines))
    return [k.create(line, voice=style, speed=speed + rng.uniform(*PACE_JITTER), lang="en-us") for line in lines]


def chatterbox_python():
    """The Python of the environment Chatterbox is installed in, or None."""
    local = os.path.join(ROOT, "voice-lab", ".venv-chatterbox", "Scripts" if os.name == "nt" else "bin", "python")
    for exe in (os.environ.get("CHATTERBOX_PYTHON"), local, local + ".exe"):
        if exe and os.path.exists(exe):
            return exe
    return None


def _chatterbox_audio(lines, voice):
    """[(audio, sample rate)] per line, spoken by Chatterbox in its own environment."""
    import soundfile as sf

    exe = chatterbox_python()
    if not exe:
        raise RuntimeError("Chatterbox is not installed (set CHATTERBOX_PYTHON)")
    cfg = CHATTERBOX[voice]
    env = dict(os.environ)
    cache = os.path.join(ROOT, "voice-lab", "hf-cache")  # a model downloaded for local tests, if there is one
    if os.path.isdir(cache) and "HF_HOME" not in env:
        env["HF_HOME"] = cache
    with tempfile.TemporaryDirectory() as tmp:
        job = os.path.join(tmp, "job.json")
        with open(job, "w", encoding="utf-8") as f:
            json.dump({"lines": lines, "out": tmp, **cfg}, f)
        script = os.path.join(ROOT, "shorts", "chatterbox_lines.py")
        subprocess.run([exe, script, job], check=True, timeout=CHATTERBOX_TIMEOUT, env=env, stdout=sys.stderr)
        out = []
        for n in range(len(lines)):
            audio, sr = sf.read(os.path.join(tmp, f"{n:02d}.wav"), dtype="float32")
            spans = _speech_spans(audio, sr)
            if not spans:
                raise RuntimeError(f"line {n + 1} came out silent")
            # Chatterbox leaves uneven silence around a line; keep a breath of it so pauses stay ours to set
            a, b = max(0, int((spans[0][0] - 0.05) * sr)), int((spans[-1][1] + 0.12) * sr)
            out.append((audio[a:b], sr))
    return out


def _join_lines(lines, out_path, line_audio):
    """Join the spoken lines with natural pauses, write the file, and time every word."""
    import soundfile as sf

    rng = random.Random(" ".join(lines))
    sr = line_audio[0][1]
    chunks, words, t = [np.zeros(int(sr * LEAD_IN), dtype=np.float32)], [], LEAD_IN
    for n, (line, (audio, sr)) in enumerate(zip(lines, line_audio)):
        spans = _speech_spans(audio, sr)
        for w in _time_line(line.split(), spans):
            words.append({"text": w["text"], "start": t + w["start"], "end": t + w["end"]})
        pause = LINE_PAUSE.get(line.rstrip()[-1:], DEFAULT_LINE_PAUSE) * rng.uniform(*PAUSE_JITTER)
        if n == 0:
            pause = HOOK_PAUSE
        chunks += [audio, np.zeros(int(sr * pause), dtype=np.float32)]
        t += len(audio) / sr + pause
    sf.write(out_path, np.concatenate(chunks), sr)
    return words


# ---------- Edge (fallback) ----------

async def _edge_async(text, voice, out_path):
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate="+4%", boundary="WordBoundary")
    words = []
    with open(out_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append({"text": chunk["text"], "start": start, "end": start + chunk["duration"] / 1e7})
    return words


def _edge(text, voice, out_path):
    return asyncio.run(_edge_async(text, voice, out_path))
