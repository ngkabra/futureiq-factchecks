#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/report.html [slug]"
  exit 1
fi

SRC="$1"
if [[ ! -f "$SRC" ]]; then
  echo "Report not found: $SRC"
  exit 1
fi

SLUG="${2:-factcheck}"
DATE="$(date +%F)"
SAFE_SLUG="$(echo "$SLUG" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9-' '-')"
DEST_NAME="$DATE-$SAFE_SLUG.html"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT_DIR/reports/$DEST_NAME"

cp "$SRC" "$DEST"
"$ROOT_DIR/generate_index.sh"

git -C "$ROOT_DIR" add reports index.html latest/index.html
if [[ -f "$ROOT_DIR/CNAME" ]]; then
  git -C "$ROOT_DIR" add CNAME
fi

git -C "$ROOT_DIR" commit -m "Publish factcheck: $DEST_NAME" || true
git -C "$ROOT_DIR" push

echo "Published: $DEST_NAME"
echo "Use /latest/ for latest redirect."
