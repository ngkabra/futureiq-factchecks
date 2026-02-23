# AGENTS

@TODO.md

## Project Description

FutureIQ Factchecks publishes self-contained HTML fact-check reports from input outlines by verifying linked claims against source content and deploying immutable report URLs via GitHub Pages.

## Goals

- Turn user-provided text or outlines into a fact-check report.
- Check only claims that have an explicit URL.
- Produce a readable standalone HTML report plus machine-readable JSON.
- Publish reports with stable, non-expiring URLs under `facts.futureiq.smritiweb.com`.

## Repository Map

- `tools/factcheck_links.py`: core generator for linked-claim fact checks.
- `reports/`: generated report artifacts (published).
- `generate_index.sh`: rebuilds site index and latest redirect.
- `publish_factcheck.sh`: copies report into `reports/`, updates index, commits, and pushes.
- `FACTCHECK.md`: operator quickstart.

## Default Agent Behavior

When user asks for a fact-check:

1. Save the provided text to a temporary file if needed.
2. Run `python3 tools/factcheck_links.py --input <file> --slug <topic> --title <title>`.
3. Share progress during long runs (fetching/evaluating many URLs).
4. Return the generated HTML path and summary counts.
5. If requested, publish via `./publish_factcheck.sh <html_path> <slug>`.

## Fact-Checking Rules

- Evaluate only lines with links.
- Treat inaccessible/paywalled/blocked pages as `insufficient` (not silently supported).
- For supported claims, include a snippet extracted from the source page.
- For unsupported claims, include why (missing numbers/details/entities).
- Preserve original claim text in output.

## Publishing and URL Policy

- Immutable published filename pattern: `YYYY-MM-DD-<slug>.html`.
- Never overwrite old report files.
- `latest/` is a redirect convenience path, not the permanent citation URL.
- Canonical permanent URLs are under `/reports/`.

## Domain and Hosting

- GitHub repo: `ngkabra/futureiq-factchecks`
- GitHub Pages custom domain: `facts.futureiq.smritiweb.com`
- CNAME target at DNS: `ngkabra.github.io`
