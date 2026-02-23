#!/usr/bin/env python3
"""Generate an HTML+JSON fact-check report from outline text.

The script extracts linked claims from text (one claim per line containing a URL),
fetches each URL, and scores whether source content supports the claim.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path
from typing import List, Tuple

import requests

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

URL_RE = re.compile(r"https?://[^\s\]\)>'\"]+")


def extract_claim_url_pairs(text: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = URL_RE.search(line)
        if not m:
            continue
        url = m.group(0).rstrip('.,);]')
        claim = line[: m.start()].strip()
        claim = re.sub(r"^[\-*+]+\s*", "", claim)
        claim = re.sub(r"\(\[\[$", "", claim).strip()
        claim = re.sub(r"\[\[\s*$", "", claim).strip()
        claim = re.sub(r"[:\-\s]+$", "", claim).strip()
        if claim:
            pairs.append((claim, url))
    return pairs


def extract_text_html(doc: str) -> tuple[str, str]:
    t = ""
    tm = re.search(r"<title[^>]*>(.*?)</title>", doc, re.I | re.S)
    if tm:
        t = re.sub(r"\s+", " ", html.unescape(tm.group(1))).strip()

    for tag in ("script", "style", "noscript"):
        doc = re.sub(rf"<{tag}\b[^<]*(?:(?!</{tag}>)<[^<]*)*</{tag}>", " ", doc, flags=re.I | re.S)

    text = re.sub(r"<[^>]+>", " ", doc)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return t, text


def key_tokens(claim: str) -> tuple[List[str], List[str]]:
    norm = re.sub(r"[^a-zA-Z0-9%$]+", " ", claim.lower())
    toks = [x for x in norm.split() if len(x) > 3 or re.match(r"\d", x)]
    stop = {
        "drone",
        "drones",
        "first",
        "using",
        "with",
        "from",
        "into",
        "that",
        "this",
        "than",
        "across",
        "their",
        "about",
        "under",
        "over",
        "now",
        "year",
        "years",
        "study",
    }
    toks = [t for t in toks if t not in stop]
    nums = re.findall(r"\$?\d+[\d,.]*(?:-\d+[\d,.]*)?%?|\d+\s?(?:km|min|million|billion|lakh|crore)", claim.lower())
    return toks[:14], nums


def fetch_url(session: requests.Session, url: str, timeout: int) -> dict:
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if resp.status_code >= 400:
            return {"ok": False, "status": resp.status_code, "title": "", "text": "", "error": f"HTTP {resp.status_code}", "final_url": resp.url}
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            return {"ok": True, "status": resp.status_code, "title": "PDF document", "text": "", "error": "PDF text extraction skipped", "final_url": resp.url}
        title, text = extract_text_html(resp.text)
        return {"ok": True, "status": resp.status_code, "title": title, "text": text, "error": "", "final_url": resp.url}
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return {"ok": False, "status": None, "title": "", "text": "", "error": str(exc), "final_url": url}


def assess_claim(claim: str, source_text: str) -> tuple[str, str, str]:
    if not source_text:
        return "insufficient", "No extractable text (paywall, block, PDF, or fetch issue).", ""

    low = source_text.lower()
    toks, nums = key_tokens(claim)
    hit_toks = [t for t in toks if t in low]
    hit_nums = [n for n in nums if n in low]

    idx = -1
    for token in hit_nums + hit_toks:
        idx = low.find(token)
        if idx != -1:
            break

    snippet = ""
    if idx != -1:
        start = max(0, idx - 180)
        end = min(len(source_text), idx + 320)
        snippet = source_text[start:end].strip()

    score = len(hit_toks) + 2 * len(hit_nums)
    if nums and not hit_nums:
        return "not_supported", "Claim has numbers not found in source text.", snippet
    if score >= 5:
        return "supported", "Core entities/details appear in source text.", snippet
    if score >= 2:
        return "partial", "Some claim elements appear; precision is incomplete.", snippet
    return "not_supported", "Source text does not clearly support this exact claim.", snippet


def build_html(results: List[dict], title: str) -> str:
    summary = {
        "total": len(results),
        "supported": sum(x["verdict"] == "supported" for x in results),
        "partial": sum(x["verdict"] == "partial" for x in results),
        "not_supported": sum(x["verdict"] == "not_supported" for x in results),
        "insufficient": sum(x["verdict"] == "insufficient" for x in results),
    }

    cards = []
    for row in results:
        cards.append(
            f"""
<section class='card {row['verdict']}'>
<div class='top'><span class='id'>{row['id']}</span><span>{row['verdict'].replace('_',' ').title()}</span></div>
<h3>{html.escape(row['claim'])}</h3>
<div class='meta'><b>Source:</b> <a href='{html.escape(row['url'])}'>{html.escape(row['url'])}</a></div>
<div class='meta'><b>Assessment:</b> {html.escape(row['reason'])}</div>
<div class='meta'><b>Fetch note:</b> {html.escape(row['error'] or 'OK')}</div>
<pre>{html.escape((row['snippet'] or '(No snippet extracted)')[:900])}</pre>
</section>
"""
        )

    return f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{html.escape(title)}</title>
<style>
body{{font-family:Arial,sans-serif;background:#f5f7fb;color:#111;padding:20px;max-width:1100px;margin:auto}}
header{{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px}}
.stat{{background:#eef2ff;border-radius:8px;padding:8px}}
.card{{background:#fff;border:1px solid #d1d5db;border-left:6px solid #9ca3af;border-radius:10px;padding:12px;margin:12px 0}}
.supported{{border-left-color:#166534;background:#ecfdf5}}
.partial{{border-left-color:#92400e;background:#fffbeb}}
.not_supported{{border-left-color:#991b1b;background:#fef2f2}}
.insufficient{{border-left-color:#1d4ed8;background:#eff6ff}}
.top{{display:flex;gap:8px;font-size:12px}} .id{{background:#111;color:#fff;padding:2px 8px;border-radius:999px}}
h3{{font-size:16px;margin:8px 0}} .meta{{font-size:13px;color:#374151;margin:4px 0}} pre{{background:#0b1020;color:#e5e7eb;padding:9px;border-radius:8px;white-space:pre-wrap}}
a{{color:#0b57d0}}
</style></head><body>
<header>
<h1>{html.escape(title)}</h1>
<p>Only lines with URLs were checked.</p>
<div class='grid'>
<div class='stat'><b>Total:</b> {summary['total']}</div>
<div class='stat'><b>Supported:</b> {summary['supported']}</div>
<div class='stat'><b>Partial:</b> {summary['partial']}</div>
<div class='stat'><b>Not supported:</b> {summary['not_supported']}</div>
<div class='stat'><b>Insufficient:</b> {summary['insufficient']}</div>
</div>
</header>
{''.join(cards)}
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to outline text/markdown file. If omitted, read stdin.")
    parser.add_argument("--slug", default="factcheck", help="Slug used in output filename.")
    parser.add_argument("--title", default="Fact Check Report", help="HTML report title.")
    parser.add_argument("--output-dir", default="reports", help="Output directory for generated files.")
    parser.add_argument("--timeout", type=int, default=12, help="Per-request timeout seconds.")
    args = parser.parse_args()

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        import sys

        text = sys.stdin.read()

    pairs = extract_claim_url_pairs(text)
    if not pairs:
        raise SystemExit("No linked claims found in input text.")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    date = dt.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9-]+", "-", args.slug.lower()).strip("-") or "factcheck"
    html_path = out_dir / f"{date}-{slug}.html"
    json_path = out_dir / f"{date}-{slug}.json"

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    results = []
    total = len(pairs)
    for idx, (claim, url) in enumerate(pairs, 1):
        fetched = fetch_url(session, url, timeout=args.timeout)
        verdict, reason, snippet = assess_claim(claim, fetched["text"])
        row = {
            "id": idx,
            "claim": claim,
            "url": url,
            "final_url": fetched.get("final_url"),
            "status": fetched.get("status"),
            "title": fetched.get("title", ""),
            "verdict": verdict,
            "reason": reason,
            "snippet": snippet,
            "error": fetched.get("error", ""),
        }
        results.append(row)
        print(f"{idx}/{total} {verdict} {url}", flush=True)

    report_html = build_html(results, args.title)
    html_path.write_text(report_html, encoding="utf-8")
    json_path.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"WROTE {html_path}")
    print(f"WROTE {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
