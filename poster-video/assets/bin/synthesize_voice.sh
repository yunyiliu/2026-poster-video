#!/usr/bin/env bash
# One-line voice synthesis for the current workspace.
#
# Override the TTS engine with env vars:
#   TTS=openai VOICE=alloy bash synthesize_voice.sh
#   TTS=say VOICE=Samantha RATE=200 bash synthesize_voice.sh
#
# The skill scripts location is auto-discovered. Override with:
#   POSTER_VIDEO_SCRIPTS=/path/to/poster-video/scripts bash synthesize_voice.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

SCRIPTS="${POSTER_VIDEO_SCRIPTS:-$HOME/.claude/skills/poster-video/scripts}"
if [ ! -f "$SCRIPTS/synthesize_voice.py" ]; then
  echo "Cannot find $SCRIPTS/synthesize_voice.py"
  echo "Set POSTER_VIDEO_SCRIPTS to the skill's scripts/ directory."
  exit 1
fi

ARGS=( "--project-dir" "$DIR" )
[ -n "$TTS" ]   && ARGS+=( "--tts" "$TTS" )
[ -n "$VOICE" ] && ARGS+=( "--voice" "$VOICE" )
[ -n "$RATE" ]  && ARGS+=( "--rate" "$RATE" )
[ -n "$SPEED" ] && ARGS+=( "--speed" "$SPEED" )

python3 "$SCRIPTS/synthesize_voice.py" "${ARGS[@]}"
