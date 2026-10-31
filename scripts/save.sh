#!/usr/bin/env bash
set -euo pipefail

MSG="${1:?Give a commit message, e.g. scripts/save.sh \"P2-T05 invoice models\"}"
BRANCH=$(git rev-parse --abbrev-ref HEAD)

case "$BRANCH" in
  person1/*) WHO=p1 ;;
  person2/*) WHO=p2 ;;
  person3/*) WHO=p3 ;;
  foundation/*) WHO="" ;;
  *) echo "You are on '$BRANCH'. Switch to your personal branch first."; exit 1 ;;
esac

if [ -n "$WHO" ]; then
  python3 scripts/check_ownership.py "$WHO"
fi

git add -A
git commit -m "$MSG" || echo "Nothing new to commit."
git push -u origin "$BRANCH"
