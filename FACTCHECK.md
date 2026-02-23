# Factcheck Workflow

## Generate a report from outline text

```bash
python3 tools/factcheck_links.py --input /path/to/outline.md --slug topic-name --title "Fact Check: Topic"
```

Outputs:
- `reports/YYYY-MM-DD-topic-name.html`
- `reports/YYYY-MM-DD-topic-name.json`

The script checks only lines that contain a URL.

## Publish to public URL (GitHub Pages)

```bash
./publish_factcheck.sh reports/YYYY-MM-DD-topic-name.html topic-name
```

After push, URLs:
- Index: `https://facts.futureiq.smritiweb.com/`
- Latest redirect: `https://facts.futureiq.smritiweb.com/latest/`
- Permanent: `https://facts.futureiq.smritiweb.com/reports/YYYY-MM-DD-topic-name.html`
