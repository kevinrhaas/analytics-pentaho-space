# analytics.pentaho.space

A living showcase of the **Pentaho Data Catalog Analytics** dashboard suite — a demonstration of
the Pentaho platform's analytical value over real catalog metadata. Every image on the site is a
**screenshot of an actual running Pentaho dashboard** (observability, governance, lineage, cost,
data quality), in both **Custom** (self-contained HTML over Pentaho CDA) and **Framework** (true
Pentaho CDF) builds.

Served via GitHub Pages from `main/` at **http://analytics.pentaho.space/**.

## How it updates
The PDC Analytics iteration loop refreshes this site at the end of each run:

```bash
./update-site.sh            # screenshots the live dashboards, regenerates index.html, commits + pushes
```

- `build/dashboards.json` — the curated dashboard manifest (stem, title, group, kind, blurb).
- `build/shots.js` — Playwright renders each dashboard on the local Pentaho server and writes
  `assets/dashboards/<stem>.png`.
- `build/gen_site.py` — regenerates `index.html` (the branded showcase) from the manifest + screenshots.

If the local server is unreachable, `update-site.sh` keeps the existing screenshots and just
regenerates and republishes. Dashboards source: [kevinrhaas/solution-engineering](https://github.com/kevinrhaas/solution-engineering)
(`iteration/v2`, deployed to `/public/pdc-iteration/v2`).

## DNS
`CNAME` → `analytics.pentaho.space`; DNS `CNAME analytics → kevinrhaas.github.io`. Pages source: `main` branch root.
