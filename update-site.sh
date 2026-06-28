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
  # resolve a playwright install (cloud images ship it at /opt/node22; else /tmp/pwshots or local).
  # shots.js takes the server URL as argv[2]; PENTAHO_PASS must be exported for the cloud server.
  PWPATH="${NODE_PATH:+$NODE_PATH:}/opt/node22/lib/node_modules:/tmp/pwshots/node_modules:$(npm root 2>/dev/null)"
  if NODE_PATH="$PWPATH" node -e "require.resolve('playwright')" 2>/dev/null; then
    NODE_PATH="$PWPATH" node build/shots.js "$SERVER" || echo "   (some shots failed; keeping prior images)"
  else
    echo "   playwright not found; installing in build/ ..."
    ( cd build && npm i playwright >/dev/null 2>&1 && npx playwright install chrome >/dev/null 2>&1 )
    ( cd build && node shots.js "$SERVER" ) || echo "   (shots failed; keeping prior images)"
  fi
else
  echo "   local server unreachable — skipping screenshots, regenerating from existing images"
fi

python3 build/gen_site.py

if [ -n "$(git status --porcelain)" ]; then
  # explicit paths only (never -A). GitHub Pages serves main/, so publish branch + main.
  BR="$(git branch --show-current)"
  git add assets/dashboards index.html build/shots.js build/dashboards.json build/gen_site.py 2>/dev/null
  git commit -q -m "Refresh dashboard showcase ($(date +%Y-%m-%d))" \
    -m "Auto-updated by the PDC Analytics loop — current dashboard screenshots + regenerated index." \
    -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  [ -n "$BR" ] && git push -q -u origin "$BR"
  # publish to main; on non-ff, fetch+merge (resolve showcase conflicts with --ours = our fresh shots) and retry
  for i in 1 2 3; do
    if git push -q origin HEAD:main; then echo "==> Published to analytics.pentaho.space"; break; fi
    git fetch -q origin
    git merge -q origin/main --no-edit 2>/dev/null || {
      git diff --name-only --diff-filter=U | while read -r f; do git checkout --ours -- "$f"; git add "$f"; done
      git commit --no-edit -q
    }
  done
else
  echo "==> No changes to publish"
fi
