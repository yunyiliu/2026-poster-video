---
name: poster-video
description: Use when the user wants to turn a set of slide / poster images into a CVPR-oral-style narrated video. The skill scaffolds a workspace, lets the agent write per-slide narration into script.md, synthesizes voice with macOS `say` or OpenAI TTS, and assembles the final MP4 with ffmpeg. Pairs naturally with the cvpr-2026-poster skill but accepts any folder of slide images.
---

# Poster / Slide → Video

## Overview

This skill turns an ordered set of slide images plus a per-slide narration
script into a single MP4 with voiceover, suitable for a 5–10 minute CVPR
oral, a workshop spotlight, or a recap clip. It is not tied to any
specific source format — pass in PNG/JPG images, get a video.

It pairs well with the `cvpr-2026-poster` skill: export the editable
poster to PDF, rasterize selected regions as slide images, then run this
skill to narrate and assemble.

## Workflow

1. Scaffold a `video-workspace/` with `init_video_project.py`.
2. Drop your slide images into `video-workspace/slides/` named in order
   (`01-title.png`, `02-problem.png`, ...).
3. Fill or generate `script.md` — one `## NN` section per slide.
4. Run `synthesize_voice.py` to convert each script section to audio.
5. Run `render_video.py` to assemble `output/poster_video.mp4`.

## Requirements

- Python 3 (preinstalled on macOS / most Linux)
- ffmpeg (`brew install ffmpeg`)
- For TTS: macOS `say` (default, free, no key) OR `OPENAI_API_KEY` for
  high-quality OpenAI TTS

## Typical prompts

- `Use $poster-video to turn the slides in ~/Desktop/my-slides into
   a 5-minute CVPR oral video.`
- `Use $poster-video to draft a per-slide narration for these images,
   matching a confident-but-clear CVPR-oral tone.`
- `Use $poster-video to re-render the video with the OpenAI TTS voice
   `alloy` and 1.05x speed.`

## Default video format

- Resolution: 1920×1080 (16:9)
- Audio: AAC 192 kbps, 44.1 kHz
- Video codec: H.264, yuv420p, ~24 fps
- Each slide held for the duration of its narration; cross-fades
  optional via `--crossfade-ms`

## Voice options

| Provider | When to use | Setup |
|----------|-------------|-------|
| macOS `say` | Free; quick draft / preview | None (built-in) |
| OpenAI TTS | Conference-grade voice for the final cut | Set `OPENAI_API_KEY` |

## Script structure

`script.md` uses one second-level heading per slide. The number must
match the image filename prefix:

```markdown
## 01

Welcome to our CVPR 2026 talk on Your Paper Title. Today we ask the
question that motivates this work, in one sentence the audience can
remember.

## 02

Cross-entropy training raises the probability of the reference token
but never suppresses the wrong token the model actually chose. ...
```

Tone guidance the agent should respect when writing the script:

- 90–120 seconds per slide for an oral talk; 20–40 seconds for a recap
- One sentence per breath group — TTS reads punctuation literally
- Spell out symbols (`p hat t`) — TTS mangles math notation
- Avoid em-dashes inside numbers (`0.143`, not `0—143`)

## Output

```
video-workspace/
├── slides/              # input images
├── script.md            # narration, one ## NN per slide
├── audio/               # one .wav or .mp3 per slide, generated
├── output/
│   └── poster_video.mp4 # final video
└── README-workspace.md
```
