# FutureIQ Factchecks

Self-contained repo for generating and publishing linked-claim fact-check reports.

## Generate fact-check report

```bash
python3 tools/factcheck_links.py --input /path/to/outline.md --slug topic-name --title "Fact Check: Topic"
```

Outputs:
- `reports/YYYY-MM-DD-topic-name.html`
- `reports/YYYY-MM-DD-topic-name.json`

## Publish to GitHub Pages

```bash
./publish_factcheck.sh reports/YYYY-MM-DD-topic-name.html topic-name
```

## URL design
- Immutable reports: `/reports/YYYY-MM-DD-slug.html`
- Latest redirect page: `/latest/index.html`
- Index: `/`

## Custom domain
- Domain: `facts.futureiq.smritiweb.com`
- CNAME target: `ngkabra.github.io`
