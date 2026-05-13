#!/usr/bin/env python3
"""Scaffold a video-workspace/ directory.

Usage:
    python3 init_video_project.py --project-dir ./video-workspace
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SUBDIRS = ["slides", "audio", "output"]

SCRIPT_TEMPLATE = """# Narration script

Each slide has its own section. The number must match the prefix of the
corresponding image in `slides/` (e.g. `## 01` pairs with `slides/01-*.png`).

The TTS engine reads punctuation literally — write the way you would
speak. Spell out math (`p hat t`, `argmax`), avoid acronyms the listener
hasn't heard before, and one sentence per breath group.

---

## 01

Welcome to our talk on Your Paper Title. Today we ask: ...

## 02

Background and motivation go here. ...

## 03

The core idea is ...
"""

WORKSPACE_README = """# Video workspace

## Inputs

- `slides/` — drop your slide images here as `01-title.png`,
  `02-problem.png`, ... (PNG / JPG, 16:9 ideally). Sorted lexicographically.
- `script.md` — narration, one `## NN` section per slide. The number
  must match the image filename prefix.

## Build

```bash
# 1. Synthesize voice for every script section
python3 path/to/poster-video/scripts/synthesize_voice.py \\
  --project-dir "$(pwd)"

# 2. Assemble the final MP4
python3 path/to/poster-video/scripts/render_video.py \\
  --project-dir "$(pwd)"
```

The final video lands at `output/poster_video.mp4`.

## TTS options

- Default: macOS `say` — free, no key, fast, draft quality.
- Better: OpenAI TTS — set `OPENAI_API_KEY` and pass `--tts openai`.
  Optional `--voice alloy|echo|fable|onyx|nova|shimmer` (default: alloy).
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Initialize a poster-video workspace.")
    p.add_argument("--project-dir", required=True, help="Target directory to create.")
    p.add_argument("--force", action="store_true", help="Allow non-empty target.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_dir).expanduser().resolve()
    skill_dir = Path(__file__).resolve().parents[1]

    if root.exists() and any(root.iterdir()) and not args.force:
        raise SystemExit(f"{root} is not empty. Pass --force to reuse it.")
    root.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)

    script_path = root / "script.md"
    if not script_path.exists():
        script_path.write_text(SCRIPT_TEMPLATE, encoding="utf-8")

    readme_path = root / "README-workspace.md"
    readme_path.write_text(WORKSPACE_README, encoding="utf-8")

    # Copy run helpers into workspace root for one-line invocations.
    bin_dir = skill_dir / "assets" / "bin"
    if bin_dir.exists():
        for item in bin_dir.iterdir():
            if item.is_file() and item.suffix == ".sh":
                dst = root / item.name
                shutil.copy2(item, dst)
                dst.chmod(0o755)

    print(f"Created video workspace at: {root}")
    print("Next steps:")
    print(f"  1. Drop slide images into {root}/slides/  (01-*.png, 02-*.png, ...)")
    print(f"  2. Fill {root}/script.md  with one ## NN section per slide")
    print(f"  3. bash {root}/synthesize_voice.sh   (or use --tts openai)")
    print(f"  4. bash {root}/render_video.sh")


if __name__ == "__main__":
    main()
