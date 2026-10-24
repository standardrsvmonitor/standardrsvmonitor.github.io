#!/bin/sh
# Fallback kicker for the public monitor. GitHub's cron fires irregularly, so this
# runs from launchd every 30 minutes and dispatches the refresh workflow whenever the
# live page is older than MAX_AGE_MIN minutes (or cannot be read). The workflow itself
# skips a run if the page is younger than 45 minutes, so a double kick is harmless.
MAX_AGE_MIN=${MAX_AGE_MIN:-75}
REPO=standardrsvmonitor/standardrsvmonitor.github.io
GH=/opt/homebrew/bin/gh
PAGE=$(curl -s -A "Mozilla/5.0" "https://standardrsvmonitor.github.io/?t=$(date +%s)")
STAMP=$(printf '%s' "$PAGE" | grep -o -E 'compiled [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} UTC' | head -1 | sed 's/compiled //; s/ UTC//')
NOW=$(date -u +%s)
if [ -n "$STAMP" ]; then
  THEN=$(date -u -j -f "%Y-%m-%d %H:%M" "$STAMP" +%s 2>/dev/null || echo 0)
  AGE=$(( (NOW - THEN) / 60 ))
else
  AGE=99999
fi
if [ "$AGE" -ge "$MAX_AGE_MIN" ]; then
  echo "$(date -u '+%F %T') page age ${AGE} min (stamp '${STAMP}'), dispatching refresh"
  "$GH" workflow run refresh.yml -R "$REPO"
else
  echo "$(date -u '+%F %T') page age ${AGE} min, fresh enough"
fi
