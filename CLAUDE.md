# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this repo is

This is **analytics.pentaho.space** — a static, single-page marketing/showcase site
served via **GitHub Pages** from the `main` branch root at
<http://analytics.pentaho.space/>. It presents the **Pentaho Data Catalog (PDC)
Analytics** dashboard suite: a curated gallery of ~50 analytical dashboards
(observability, governance, lineage, cost, data quality, glossary/stewardship),
each shown as a **real screenshot of an actual running Pentaho dashboard**.

This repo is the *publishing surface only*. It does **not** contain the dashboards
themselves. The dashboards live in a separate repo,
[kevinrhaas/solution-engineering](https://github.com/kevinrhaas/solution-engineering)
(`iteration/v2`, deployed to a Pentaho server at `/public/pdc-iteration/v2`). This
repo screenshots them and renders a branded `index.html` gallery around the images.

Each dashboard exists in two "builds": **Custom** (self-contained HTML over Pentaho
CDA, badged "Classic HTML") and **Framework** (a true Pentaho CDF dashboard with CCC
charts, badged "Framework · CDF"). A few are authored CDE boards (`.wcdf`/`.cdfde`).

## Repository layout

```
.
├── index.html              # The published site. GENERATED — do not hand-edit (see below).
├── CNAME                   # GitHub Pages custom domain: analytics.pentaho.space
├── README.md               # Human-facing overview of how the site updates
├── update-site.sh          # Top-level entry point: screenshot → regenerate → commit → push
├── assets/
│   ├── dashboards/<stem>.jpg   # Full-page dashboard screenshots used in the gallery
│   └── thumbs/<stem>.jpg       # Small launcher thumbnails (consumed by the upstream launcher)
└── build/
    ├── dashboards.json     # The curated manifest — source of truth for what appears on the site
    ├── gen_site.py         # Renders index.html from dashboards.json + assets/dashboards/*.jpg
    ├── shots.js            # Playwright: screenshots each dashboard into assets/dashboards/
    ├── thumbs.js           # Playwright: captures launcher thumbnails into assets/thumbs/
    ├── launcher-stems.txt  # Stem list (one per line) for thumbs.js
    ├── package-lock.json   # Pins playwright for the build scripts
    └── node_modules/       # Vendored playwright — committed to the repo (no .gitignore)
```

## How the site is built and published

The whole pipeline is one command, normally run at the end of each "PDC Analytics
loop" run:

```bash
./update-site.sh [SERVER]      # default SERVER = http://localhost:8080/pentaho
```

`update-site.sh` does, in order:
1. **Probe** the local Pentaho server (`$SERVER/Login`). If it is reachable:
2. **Screenshot** every dashboard via `build/shots.js` (Playwright + Chrome),
   writing `assets/dashboards/<stem>.jpg`. If the server is **unreachable**, this
   step is skipped and the existing screenshots are kept.
3. **Regenerate** `index.html` from the manifest via `python3 build/gen_site.py`.
4. **Commit + push** to `main` only if `git status --porcelain` shows changes.
   Commit message is `Refresh dashboard showcase (YYYY-MM-DD)`.

`build/shots.js` details: authenticates to Pentaho via
`POST /j_spring_security_check` (admin/password), then loads each dashboard at
`{server}/api/repos/{repo}{stem}.html/content`, waits ~3.8s for charts to draw, and
saves a JPEG (quality 80; full-page for gallery items, viewport for the launcher).
`server` and `repo` come from `dashboards.json`.

`build/gen_site.py` details: reads `dashboards.json`, emits a fully self-contained
`index.html` (all CSS/JS inline — no external assets except the screenshots). It
builds a filter toolbar (search + area chips + build-type chips), the dashboard
grid grouped by area, and a "What's new" changelog auto-derived from the **sibling
`../solution-engineering` git history** (`iteration/` commits). The changelog
silently degrades to empty if that sibling repo is not present — it never fails the
build.

## The manifest: `build/dashboards.json`

This is the **source of truth** for what appears on the site. To add, remove, retitle,
or recategorize a dashboard, edit this file — never edit `index.html` directly.

Shape:
- `server`, `repo` — where `shots.js`/`thumbs.js` fetch dashboards from.
- `launcher` — `{ stem, title, blurb }` for the hero image (uses `assets/dashboards/<stem>.jpg`).
- `groups[]` — each `{ name, value, items[] }`. `value` is the group's one-line pitch.
  - `items[]` — each `{ stem, title, kind, blurb, value }`.
    - `stem` — filename stem; the screenshot must exist at `assets/dashboards/<stem>.jpg`.
    - `kind` — `"Custom"` (→ "Classic HTML" badge) or `"Framework"` (→ "Framework · CDF").
    - `blurb` — short card description; `value` — the business-value line on the card.

A `stem` with no matching `assets/dashboards/<stem>.jpg` renders as a "screenshot
pending" placeholder — it does not break the build.

## Key conventions and gotchas

- **`index.html` is generated.** Treat it as a build artifact. Any manual edit will be
  overwritten on the next `gen_site.py` run. Change `gen_site.py` (template/logic) or
  `dashboards.json` (content) instead, then regenerate.
- **Screenshots are `.jpg`.** The current pipeline writes JPEGs (`gen_site.py` looks
  for `assets/dashboards/%s.jpg`). The README still says "PNG" in places — that wording
  is stale; the actual files are `.jpg`.
- **`node_modules/` is committed.** There is no `.gitignore`; `build/node_modules`
  (vendored Playwright) is tracked in git. Avoid noisy churn there — don't reinstall or
  upgrade unless that is the task. `update-site.sh` reuses an existing Playwright
  install (`/tmp/pwshots` or local) and only installs if none is found.
- **Server-dependent steps degrade gracefully.** `shots.js`/`thumbs.js` need a live
  Pentaho server at `localhost:8080` with the v2 suite deployed. In an environment
  without it, only `gen_site.py` will do useful work (regenerate from existing images).
  Don't treat "server unreachable" as a failure — it's an expected path.
- **Changelog depends on a sibling repo.** `gen_site.py` reads `../solution-engineering`
  git log. If absent, the "What's new" section is simply omitted.
- **Hero/launcher** image uses the `launcher.stem` screenshot (`i-home`).
- **`thumbs.js` is for the upstream launcher**, not this site's gallery — `index.html`
  does not reference `assets/thumbs/`. It captures CDE boards (`cde-*` stems) via
  `.wcdf/generatedContent` and everything else via `.html/content`.

## Working in this repo

- **Editing site content/structure** → edit `build/dashboards.json`, then run
  `python3 build/gen_site.py` to regenerate `index.html`. Review the diff before committing.
- **Editing site styling/layout/copy** → edit the inline template inside
  `build/gen_site.py`, then regenerate.
- **Refreshing screenshots** → requires a running Pentaho server; run
  `./update-site.sh` (or `node build/shots.js` from `build/`).
- **Just regenerating without screenshots** (e.g. after a manifest edit, no server) →
  `python3 build/gen_site.py`.

### Verifying a change locally

```bash
python3 build/gen_site.py          # regenerate index.html from the manifest
python3 -m http.server 8000        # then open http://localhost:8000/ to eyeball it
```

There is no test suite, linter, or CI in this repo. Verification is visual: regenerate
and look at `index.html` / the rendered page.

## Git workflow

- The published branch is **`main`** (GitHub Pages serves from `main` root).
  `update-site.sh` commits and pushes to `main` automatically.
- For task work driven by an assistant, develop on the assigned feature branch and
  push there; do **not** push to `main` without explicit permission. Do not open a PR
  unless explicitly asked.
- Keep commits scoped. Regenerating `index.html` after a manifest/template change is
  expected and should be committed together with the source change so the artifact
  stays in sync.
