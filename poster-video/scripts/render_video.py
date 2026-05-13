#!/usr/bin/env python3
"""Assemble slides + per-slide audio into a single MP4 with ffmpeg.

For each matching pair (slides/NN-*.{png,jpg} + audio/NN.{aiff,mp3,wav}):
  - Produce an intermediate clip that shows the slide for the length of
    the audio (with the audio attached).
Then concatenate every clip in numeric order into output/poster_video.mp4.

Usage:
    python3 render_video.py --project-dir ./video-workspace
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

SLIDE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
AUDIO_EXTS = (".aiff", ".mp3", ".wav", ".m4a")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render slides + audio into MP4.")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--crossfade-ms", type=int, default=0,
                   help="Cross-fade duration between slides in ms (0 = hard cuts).")
    p.add_argument("--output", default=None, help="Override output path.")
    return p.parse_args()


def find_pairs(slides_dir: Path, audio_dir: Path) -> list[tuple[str, Path, Path]]:
    by_num_slide: dict[str, Path] = {}
    by_num_audio: dict[str, Path] = {}
    for f in slides_dir.iterdir():
        if f.is_file() and f.suffix.lower() in SLIDE_EXTS:
            num = f.stem.split("-", 1)[0].zfill(2)
            by_num_slide.setdefault(num, f)
    for f in audio_dir.iterdir():
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS:
            num = f.stem.split("-", 1)[0].zfill(2)
            by_num_audio.setdefault(num, f)

    pairs: list[tuple[str, Path, Path]] = []
    for num in sorted(set(by_num_slide) & set(by_num_audio)):
        pairs.append((num, by_num_slide[num], by_num_audio[num]))
    missing_audio = sorted(set(by_num_slide) - set(by_num_audio))
    missing_slide = sorted(set(by_num_audio) - set(by_num_slide))
    if missing_audio:
        print(f"  warning: slides without audio: {missing_audio}")
    if missing_slide:
        print(f"  warning: audio without slides: {missing_slide}")
    return pairs


def encode_clip(slide: Path, audio: Path, out: Path, width: int, height: int, fps: int) -> None:
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:white,"
        f"setsar=1,fps={fps}"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(slide),
        "-i", str(audio),
        "-c:v", "libx264", "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-vf", vf,
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)


def concat_clips(clips: list[Path], out: Path, crossfade_ms: int, fps: int) -> None:
    if crossfade_ms <= 0:
        # Fast path: stream copy via concat demuxer
        list_file = out.with_suffix(".txt")
        list_file.write_text(
            "\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8"
        )
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", "-movflags", "+faststart",
            str(out),
        ]
        subprocess.run(cmd, check=True)
        list_file.unlink(missing_ok=True)
        return

    # Crossfade path: build filter_complex with xfade per transition.
    cf = crossfade_ms / 1000.0
    durations = []
    for c in clips:
        out_p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(c)],
            check=True, capture_output=True, text=True,
        )
        durations.append(float(out_p.stdout.strip()))

    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", str(c)]
    filters: list[str] = []
    last = "[0:v]"
    last_a = "[0:a]"
    offset = durations[0] - cf
    for i in range(1, len(clips)):
        filters.append(
            f"{last}[{i}:v]xfade=transition=fade:duration={cf}:offset={offset:.3f}[v{i}]"
        )
        filters.append(
            f"{last_a}[{i}:a]acrossfade=d={cf}[a{i}]"
        )
        last = f"[v{i}]"
        last_a = f"[a{i}]"
        offset += durations[i] - cf
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", last, "-map", last_a,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    args = parse_args()
    root = Path(args.project_dir).expanduser().resolve()
    slides_dir = root / "slides"
    audio_dir = root / "audio"
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    final = Path(args.output) if args.output else (out_dir / "poster_video.mp4")

    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. `brew install ffmpeg` and retry.")
    if not slides_dir.exists():
        raise SystemExit(f"Missing {slides_dir}")
    if not audio_dir.exists() or not any(audio_dir.iterdir()):
        raise SystemExit(f"Missing {audio_dir} or it is empty — run synthesize_voice.py first.")

    pairs = find_pairs(slides_dir, audio_dir)
    if not pairs:
        raise SystemExit("No matching slide/audio pairs found.")

    tmp = root / ".video-tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    clip_paths: list[Path] = []
    try:
        for num, slide, audio in pairs:
            clip = tmp / f"clip-{num}.mp4"
            print(f"  encoding clip {num}: {slide.name} + {audio.name}")
            encode_clip(slide, audio, clip, args.width, args.height, args.fps)
            clip_paths.append(clip)
        print(f"  concatenating {len(clip_paths)} clips...")
        concat_clips(clip_paths, final, args.crossfade_ms, args.fps)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"Wrote {final}")


if __name__ == "__main__":
    main()
