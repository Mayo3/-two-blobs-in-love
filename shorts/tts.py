"""Text-to-speech with per-word timings for captions.

Default voice engine is Kokoro (open-source, runs locally, sounds natural). Kokoro gives
no word timings, so we synthesize line by line, find the pauses in each line's audio,
match them to its punctuation, and spread words between pauses by phoneme count.
Edge TTS (voice names starting with "en-") is kept as a fallback.
"""
import asyncio
import os
import random
import re

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, "models", "kokoro-v1.0.onnx")
VOICES_BIN = os.path.join(ROOT, "models", "voices-v1.0.bin")
LINE_PAUSE = {".": 0.42, "?": 0.48, "!": 0.42, "…": 0.5}  # silence after a line, by its last char
DEFAULT_LINE_PAUSE = 0.3
LEAD_IN = 0.15  # just enough silence that players don't clip the first word
SPEED = 0.92  # a little slower than default reads calmer and more natural
# a person never reads every line at the same pace or pauses the same length; small random
# changes per line make the narration sound much less robotic (seeded by the script, so repeatable)
PACE_JITTER = (-0.04, 0.05)  # added to SPEED per line
PAUSE_JITTER = (0.75, 1.35)  # multiplies the pause after each line
# custom voices: weighted mixes of Kokoro's built-in voices
BLENDS = {"heart-nova": {"af_heart": 0.6, "af_nova": 0.4}}

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
    if voice.startswith("en-"):
        return _edge(" ".join(lines), voice, out_path)
    return _kokoro_lines(lines, voice, out_path, speed)


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


def _kokoro_lines(lines, voice, out_path, speed):
    import soundfile as sf

    k = _engine()
    style = sum(w * k.get_voice_style(n) for n, w in BLENDS[voice].items()) if voice in BLENDS else voice
    rng = random.Random(" ".join(lines))
    sr = 24000
    chunks, words, t = [np.zeros(int(sr * LEAD_IN), dtype=np.float32)], [], LEAD_IN
    for line in lines:
        audio, sr = k.create(line, voice=style, speed=speed + rng.uniform(*PACE_JITTER), lang="en-us")
        spans = _speech_spans(audio, sr)
        for w in _time_line(line.split(), spans):
            words.append({"text": w["text"], "start": t + w["start"], "end": t + w["end"]})
        pause = LINE_PAUSE.get(line.rstrip()[-1:], DEFAULT_LINE_PAUSE) * rng.uniform(*PAUSE_JITTER)
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
