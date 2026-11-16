"""Background music: a soft lo-fi track under the voices, for the platforms the video is posted to automatically
(YouTube, Instagram, Facebook). TikTok gets the version without it, so a trending sound can be added there.

The tracks in music/ were made with ACE-Step 1.5 (voice-lab/music_gen.py), whose licence allows commercial use of
what it generates, so no one else's Content ID can claim them. The music ducks whenever Pip or Bo speak.
"""
import os
import random
import subprocess

from .render import audio_duration, ffmpeg_exe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_DIR = os.path.join(ROOT, "music")
LEVEL = 1.13  # the track's loudness before ducking (chosen by ear on 2026-11-16)
VOICE = 0.5  # Pip and Bo 6 dB quieter than in the TikTok version, so the music carries (chosen by ear)
FADE_IN, FADE_OUT = 1.0, 2.0


def tracks():
    if not os.path.isdir(MUSIC_DIR):
        return []
    return sorted(os.path.join(MUSIC_DIR, f) for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".m4a", ".wav")))


def pick(n):
    """The track for the n-th video: they take turns, so two videos in a row never share one."""
    found = tracks()
    return found[n % len(found)] if found else None


def add_music(video, track, out, seed=""):
    """`video` with `track` mixed quietly under its voice, written to `out`. The music starts at a random
    point of the track (by `seed`), so a track sounds a little different each time it comes back."""
    length = audio_duration(video)
    room = max(0.0, audio_duration(track) - length - 1)
    start = random.Random(f"music {seed}").uniform(0, min(room, 30.0))
    graph = (
        f"[0:a]aresample=48000,asplit=2[speech][key];[speech]volume={VOICE}[voice];"
        f"[1:a]aresample=48000,volume={LEVEL},afade=t=in:d={FADE_IN},"
        f"afade=t=out:st={max(0.0, length - FADE_OUT):.2f}:d={FADE_OUT}[bed];"
        # duck the music while someone speaks, let it come back up in the pauses
        "[bed][key]sidechaincompress=threshold=0.03:ratio=2:attack=20:release=400[ducked];"
        "[voice][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.9:level=disabled[mix]"  # a safety net: loud moments can never distort
    )
    subprocess.run([
        ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", video, "-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", track,
        "-filter_complex", graph, "-map", "0:v", "-map", "[mix]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{length:.2f}", "-movflags", "+faststart", out,
    ], check=True)
    return out
