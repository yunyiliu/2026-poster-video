#!/usr/bin/env bash
# Assemble slides + audio into output/poster_video.mp4
#
# Env overrides:
#   CROSSFADE_MS=400 bash render_video.sh
#   WIDTH=1920 HEIGHT=1080 FPS=30 bash render_video.sh
#   POSTER_VIDEO_SCRIPTS=/path/to/poster-video/scripts bash render_video.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

SCRIPTS="${POSTER_VIDEO_SCRIPTS:-$HOME/.claude/skills/poster-video/scripts}"
if [ ! -f "$SCRIPTS/render_video.py" ]; then
  echo "Cannot find $SCRIPTS/render_video.py"
  echo "Set POSTER_VIDEO_SCRIPTS to the skill's scripts/ directory."
  exit 1
fi

ARGS=( "--project-dir" "$DIR" )
[ -n "$WIDTH" ]        && ARGS+=( "--width" "$WIDTH" )
[ -n "$HEIGHT" ]       && ARGS+=( "--height" "$HEIGHT" )
[ -n "$FPS" ]          && ARGS+=( "--fps" "$FPS" )
[ -n "$CROSSFADE_MS" ] && ARGS+=( "--crossfade-ms" "$CROSSFADE_MS" )
[ -n "$OUTPUT" ]       && ARGS+=( "--output" "$OUTPUT" )

python3 "$SCRIPTS/render_video.py" "${ARGS[@]}"
