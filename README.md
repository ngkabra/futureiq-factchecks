# FutureIQ Factcheck Pages

Static GitHub Pages site for publishing fact-check HTML reports with stable URLs.

## URL design
- Immutable reports: `/reports/YYYY-MM-DD-slug.html`
- Latest redirect page: `/latest/index.html`
- Index: `/`

## One-command publish
From this repo:

```bash
./publish_factcheck.sh /path/to/generated_report.html optional-slug
```

Example:

```bash
./publish_factcheck.sh ../drone_outline_factcheck.html drone-applications
```

## Custom domain
Set repository Pages custom domain to `facts.futureiq.smritiweb.com` and keep `CNAME` file in repo.
