#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
LATEST_DIR="$ROOT_DIR/latest"
mkdir -p "$REPORTS_DIR" "$LATEST_DIR"

TMP_LIST="$(mktemp)"
find "$REPORTS_DIR" -maxdepth 1 -type f -name '*.html' -printf '%f\n' | sort -r > "$TMP_LIST"

{
  echo '<!doctype html>'
  echo '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
  echo '<title>FutureIQ Fact Checks</title>'
  echo '<style>body{font-family:Arial,sans-serif;background:#f5f7fb;color:#111;padding:24px;max-width:900px;margin:auto}h1{margin-bottom:8px}a{color:#0b57d0;text-decoration:none}a:hover{text-decoration:underline}.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px;margin:10px 0}</style>'
  echo '</head><body>'
  echo '<h1>FutureIQ Fact Checks</h1>'
  echo '<p>Permanent report links (newest first).</p>'

  if [[ -s "$TMP_LIST" ]]; then
    while IFS= read -r fname; do
      safe="${fname%.html}"
      echo "<div class='card'><a href='reports/$fname'>$safe</a></div>"
    done < "$TMP_LIST"
  else
    echo '<p>No reports published yet.</p>'
  fi

  echo '</body></html>'
} > "$ROOT_DIR/index.html"

LATEST_FILE="$(head -n 1 "$TMP_LIST" || true)"
if [[ -n "$LATEST_FILE" ]]; then
  cat > "$LATEST_DIR/index.html" <<HTML
<!doctype html>
<html><head>
<meta http-equiv="refresh" content="0; url=../reports/$LATEST_FILE">
<title>Latest Fact Check</title>
</head><body>
<p>Redirecting to latest report: <a href="../reports/$LATEST_FILE">$LATEST_FILE</a></p>
</body></html>
HTML
else
  cat > "$LATEST_DIR/index.html" <<'HTML'
<!doctype html>
<html><head><title>No reports yet</title></head><body><p>No reports published yet.</p></body></html>
HTML
fi

rm -f "$TMP_LIST"
echo "Index generated."
