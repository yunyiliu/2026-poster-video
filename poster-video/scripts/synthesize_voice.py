#!/usr/bin/env python3
"""Read script.md and produce one audio file per `## NN` section.

Defaults to macOS `say` (free, no API key). Pass `--tts openai` to use
the OpenAI text-to-speech endpoint instead (requires OPENAI_API_KEY).

Usage:
    python3 synthesize_voice.py --project-dir ./video-workspace
    python3 synthesize_voice.py --project-dir ./video-workspace --tts openai --voice alloy
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Synthesize narration audio per slide.")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--tts", choices=["say", "openai"], default="say")
    p.add_argument("--voice", default=None,
                   help="`say`: e.g. Samantha, Daniel. `openai`: alloy|echo|fable|onyx|nova|shimmer")
    p.add_argument("--rate", type=int, default=180,
                   help="Words per minute for macOS `say` (ignored for openai).")
    p.add_argument("--openai-model", default="tts-1-hd",
                   help="OpenAI TTS model (e.g. tts-1, tts-1-hd, gpt-4o-mini-tts).")
    p.add_argument("--speed", type=float, default=1.0,
                   help="OpenAI TTS speech rate, 0.25–4.0.")
    return p.parse_args()


SECTION_RE = re.compile(r"^##\s+(\d+)\b(.*)$")


def parse_script(path: Path) -> list[tuple[str, str]]:
    """Return [(slide_number, text), ...] in input order."""
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = SECTION_RE.match(raw.strip())
        if m:
            if current:
                sections.append(current)
            current = (m.group(1), [])
            continue
        if current is None:
            continue
        current[1].append(raw)
    if current:
        sections.append(current)
    return [(num, "\n".join(lines).strip()) for num, lines in sections if "\n".join(lines).strip()]


def synth_say(text: str, out: Path, voice: str | None, rate: int) -> None:
    cmd = ["say", "-r", str(rate), "-o", str(out)]
    if voice:
        cmd += ["-v", voice]
    cmd += [text]
    subprocess.run(cmd, check=True)


def synth_openai(text: str, out: Path, model: str, voice: str | None, speed: float) -> None:
    import urllib.request
    import json

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set. `export OPENAI_API_KEY=sk-...` first.")

    body = {
        "model": model,
        "voice": voice or "alloy",
        "input": text,
        "speed": speed,
        "format": "mp3",
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        out.write_bytes(resp.read())


def main() -> None:
    args = parse_args()
    root = Path(args.project_dir).expanduser().resolve()
    script_path = root / "script.md"
    audio_dir = root / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    if not script_path.exists():
        raise SystemExit(f"Missing {script_path}")

    if args.tts == "say" and not shutil.which("say"):
        raise SystemExit("`say` not found. This default voice is macOS-only. Try `--tts openai`.")

    sections = parse_script(script_path)
    if not sections:
        raise SystemExit("No `## NN` sections found in script.md")

    ext = "aiff" if args.tts == "say" else "mp3"
    print(f"Synthesizing {len(sections)} sections via {args.tts}...")
    for num, text in sections:
        out = audio_dir / f"{num.zfill(2)}.{ext}"
        print(f"  -> {out.name}  ({len(text)} chars)")
        if args.tts == "say":
            synth_say(text, out, args.voice, args.rate)
        else:
            synth_openai(text, out, args.openai_model, args.voice, args.speed)

    print(f"Wrote {len(sections)} audio file(s) into {audio_dir}")


if __name__ == "__main__":
    main()
