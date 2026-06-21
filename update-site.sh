#!/usr/bin/env bash
# update-site.sh — refresh analytics.pentaho.space with current dashboard screenshots and
# regenerate index.html, then commit + push (GitHub Pages serves main/). Called at the END
# of each PDC Analytics loop run. Safe to run anytime; if the local Pentaho server is down it
# keeps the existing screenshots and just regenerates + publishes.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
SERVER="${1:-http://localhost:8080/pentaho}"

echo "==> Refreshing analytics.pentaho.space"
if curl -s -o /dev/null --max-time 8 "$SERVER/Login"; then
  # resolve a playwright install (reuse /tmp/pwshots if present, else local)
  if NODE_PATH="/tmp/pwshots/node_modules:$(npm root 2>/dev/null)" node -e "require.resolve('playwright')" 2>/dev/null; then
    NODE_PATH="/tmp/pwshots/node_modules:$(npm root 2>/dev/null)" node build/shots.js || echo "   (some shots failed; keeping prior images)"
  else
    echo "   playwright not found; installing in build/ ..."
    ( cd build && npm i playwright >/dev/null 2>&1 && npx playwright install chrome >/dev/null 2>&1 )
    ( cd build && node shots.js ) || echo "   (shots failed; keeping prior images)"
  fi
else
  echo "   local server unreachable — skipping screenshots, regenerating from existing images"
fi

python3 build/gen_site.py

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -q -m "Refresh dashboard showcase ($(date +%Y-%m-%d))" \
    -m "Auto-updated by the PDC Analytics loop — current dashboard screenshots + regenerated index." \
    -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  git push -q origin main && echo "==> Published to analytics.pentaho.space"
else
  echo "==> No changes to publish"
fi
