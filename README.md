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

Install the runtime dependencies (one time):

```bash
brew install ffmpeg poppler              # video assembly + PDF rasterizer
brew install --cask libreoffice           # PPTX/Keynote -> PDF converter
```

`ffmpeg` is required. `poppler` is needed if you want the skill to
auto-import a `.pptx`, `.key`, or `.pdf` deck. `libreoffice` is the
most reliable `.pptx` converter; on macOS you can skip it if Keynote
opens your file cleanly.

Start a new Claude Code session. The skill appears as `poster-video`
in the available-skills list.

### 2. Ask the agent

Pick the prompt that matches what you have on disk:

**You have a `.pptx` and a paper LaTeX file:**

> Use `$poster-video` to scaffold a video workspace at
> `~/Desktop/my-poster-video/`. Import the deck at
> `/path/to/deck.pptx` via `import_deck.py`. Then read
> `/path/to/paper/main.tex` and write a 6-slide, 5-minute CVPR
> oral script (one `## NN` section per slide). Synthesize voice
> with macOS `say`, then render the final MP4.

**You only have a slide-deck PDF:**

> Use `$poster-video` to scaffold a video workspace at
> `~/Desktop/my-poster-video/`. Import the deck at
> `/path/to/deck.pdf` via `import_deck.py`. Then read my paper at
> `/path/to/paper/main.tex` and write a 5-minute, 6-slide CVPR oral
> script. Use OpenAI TTS with voice `alloy`, then render the MP4.

**You already have slide images:**

> Use `$poster-video` to scaffold a video workspace at
> `~/Desktop/my-poster-video/`. Copy the slide PNGs from
> `~/Desktop/exported-slides/` into the workspace's `slides/`
> folder. Then write a 6-slide, 5-minute CVPR oral script based on
> the paper at `/path/to/paper/main.tex` and render the MP4.

**Re-render only (you tweaked `script.md`):**

> Use `$poster-video` to re-synthesize voice and re-render the
> video in `~/Desktop/my-poster-video/` using OpenAI TTS voice
> `nova` at 1.05x speed, with 400ms crossfades between slides.

The agent will:

- Run `init_video_project.py` to create the workspace skeleton
- Help you write `script.md` (one `## NN` section per slide)
- Drop slide PNGs into `slides/`. You can either:
  - Hand it your own PNGs/JPGs, or
  - Hand it a `.pptx`, `.key`, or `.pdf` file — the skill auto-converts
    via LibreOffice / Keynote / pdftoppm into one PNG per page.

Paper PDFs work as input too — the agent can read the text from the
LaTeX source or the PDF to write the script, while either rasterizing
the paper pages as slide visuals or pointing at separately rendered
slide images.

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
- For PPTX/PDF deck import: poppler (`brew install poppler`) — gives
  `pdftoppm`. For PPTX specifically you also need LibreOffice
  (`brew install --cask libreoffice`) or macOS Keynote.
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
