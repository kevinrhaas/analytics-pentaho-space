# analytics.pentaho.space

Static public briefing site for the Pentaho Data Catalog analytics suite deployed locally at `/public/pdc-iteration/v1`.

## Source evidence

- Pentaho User Console: `http://localhost:8080/pentaho/Home`
- Repository folder API: `/pentaho/plugin/scheduler-plugin/api/generic-files/:public:pdc-iteration:v1`
- Local source export: `solution-engineering/iteration/v1`
- Core live metrics came from CDA `doQuery` calls against `pdc-command-center.cda`, `lineage-explorer.cda`, and related v1 dashboard descriptors.

## DNS target

The repo includes `CNAME` with `analytics.pentaho.space`. For GitHub Pages, configure the DNS provider with:

- `CNAME analytics kevinrhaas.github.io`

If GoDaddy does not allow that exact host form, use host/name `analytics` and value `kevinrhaas.github.io`.
