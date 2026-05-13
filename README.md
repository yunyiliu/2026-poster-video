# Poster Video Skill

Turn a folder of slide images + a written script into a narrated CVPR
oral video, end to end. Uses macOS `say` or OpenAI TTS for voice, and
ffmpeg to assemble the final MP4.

Designed as a Claude Code / Codex **skill**, not a standalone CLI tool.
Pairs naturally with [cvpr-2026-poster](https://github.com/yunyiliu/cvpr-2026-poster-skill):
generate a poster, rasterize the cards as slide images, then run this
skill to narrate and render.

---

## How to start

### 1. Install the skill (one time)

```bash
git clone https://github.com/yunyiliu/2026-poster-video.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/2026-poster-video/poster-video" ~/.claude/skills/poster-video
```

Install ffmpeg (one time):

```bash
brew install ffmpeg
```

Start a new Claude Code session. The skill appears as `poster-video`
in the available-skills list.

### 2. Ask the agent

> Use `$poster-video` to scaffold a video workspace at
> `~/Desktop/sat-rrg-video/`. I'll drop my slide images into
> `slides/`. Then write a 6-slide, 5-minute CVPR oral script based on
> my paper draft at `~/papers/foo/main.tex`.

The agent will:

- Run `init_video_project.py` to create the workspace skeleton
- Help you write `script.md` (one `## NN` section per slide)
- Tell you to drop slide PNGs into `slides/`

### 3. Synthesize voice

```bash
cd video-workspace
bash synthesize_voice.sh                   # macOS `say`, free
# or:
TTS=openai VOICE=alloy bash synthesize_voice.sh   # needs OPENAI_API_KEY
```

### 4. Render the video

```bash
bash render_video.sh
# with crossfades:
CROSSFADE_MS=400 bash render_video.sh
```

Output lands at `video-workspace/output/poster_video.mp4`.

---

## What you need

- Python 3
- ffmpeg (`brew install ffmpeg`)
- For higher-quality voice: `OPENAI_API_KEY` (set in your shell)

---

## What gets created

```
video-workspace/
├── slides/              ← drop slide images here (01-*.png, 02-*.png, ...)
├── script.md            ← narration, one ## NN section per slide
├── audio/               ← per-slide audio (generated)
├── output/
│   └── poster_video.mp4 ← final video
├── README-workspace.md
├── synthesize_voice.sh  ← one-line TTS
└── render_video.sh      ← one-line ffmpeg assembly
```

---

## Script tone tips

The TTS engine reads punctuation literally, so write the way you speak:

- One sentence per breath group
- Spell out math (`p hat t`, `argmax over v`) — symbols mangle
- Numbers go through fine: `0.143`, `42 percent`
- 90–120 seconds per slide for a 5-minute oral

The bundled `assets/examples/script-template.md` is a starting point.

---

## Voice options

| Engine | Setup | When |
|--------|-------|------|
| macOS `say` (default) | Built-in on macOS | Free draft / preview |
| OpenAI TTS | `export OPENAI_API_KEY=...` | Conference-grade final cut |

For OpenAI, override voice with `VOICE=alloy|echo|fable|onyx|nova|shimmer`,
or speech rate with `SPEED=1.05`.

---

## Without an AI agent

Drive the scripts directly:

```bash
python3 poster-video/scripts/init_video_project.py --project-dir ./video-workspace
# drop slides into ./video-workspace/slides/
# fill ./video-workspace/script.md
python3 poster-video/scripts/synthesize_voice.py --project-dir ./video-workspace
python3 poster-video/scripts/render_video.py --project-dir ./video-workspace
```

---

## License

MIT. See [LICENSE](LICENSE).
