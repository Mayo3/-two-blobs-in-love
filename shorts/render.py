"""Renders the final vertical video with ffmpeg: cartoon (or stock footage) frames,
captions and the normalised voice track.
"""
import os
import re
import shutil
import subprocess

from .captions import PALETTES, W, H

FPS = 30
# Even loudness at the level Shorts/TikTok expect, then pad so the video can outlast the voice.
AUDIO_FILTER = "loudnorm=I=-14:TP=-1.5:LRA=11,apad"


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg  # bundled binary for machines without ffmpeg installed
    return imageio_ffmpeg.get_ffmpeg_exe()


def audio_duration(path):
    out = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    if not m:
        raise RuntimeError(f"could not read duration of {path}")
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def render_cartoon(workdir, audio_name, ass_name, out_path, palette, duration, fonts_dir, animator):
    """Draw the cartoon frame by frame and pipe raw frames into ffmpeg with captions and voice."""
    from .cartoon.director import render_frames

    rel_fonts = os.path.relpath(fonts_dir, workdir).replace("\\", "/")
    graph = f"[0]format=yuv420p,ass={ass_name}:fontsdir={rel_fonts}[v]"
    cmd = [
        ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", audio_name,
        "-filter_complex", graph,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-af", AUDIO_FILTER, "-t", f"{duration:.3f}",
        "-movflags", "+faststart",
        os.path.abspath(out_path),
    ]
    proc = subprocess.Popen(cmd, cwd=workdir, stdin=subprocess.PIPE)
    try:
        render_frames(animator, duration, FPS, proc.stdin.write)
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")


def render_footage(workdir, audio_name, ass_name, out_path, palette, duration, fonts_dir, clips, segments):
    """Cut one stock clip per segment, crop to vertical, grade gently, then captions and voice."""
    rel_fonts = os.path.relpath(fonts_dir, workdir).replace("\\", "/")
    inputs, parts = [], []
    for i, (path, (start, end)) in enumerate(zip(clips, segments)):
        seg = end - start
        inputs += ["-stream_loop", "-1", "-t", f"{seg + 0.2:.3f}", "-i", path]
        parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
            f"trim=duration={seg:.3f},setpts=PTS-STARTPTS[c{i}]"
        )
    n = len(clips)
    graph = ";".join(parts) + ";" + "".join(f"[c{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
    # Slightly darker and warmer so white captions always read, plus a soft vignette.
    graph += f"eq=brightness=-0.07:saturation=1.05:gamma_r=1.03,vignette=PI/4.2,format=yuv420p[bg];"
    graph += f"[bg]ass={ass_name}:fontsdir={rel_fonts}[v]"
    cmd = [
        ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-i", audio_name,
        "-filter_complex", graph,
        "-map", "[v]", "-map", f"{n}:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-af", AUDIO_FILTER, "-t", f"{duration:.3f}",
        "-movflags", "+faststart",
        os.path.abspath(out_path),
    ]
    subprocess.run(cmd, cwd=workdir, check=True)
