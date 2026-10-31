#!/usr/bin/env bash
set -euo pipefail

BRANCH=$(git rev-parse --abbrev-ref HEAD)
git diff --quiet && git diff --cached --quiet || { echo "Save your work first (scripts/save.sh)."; exit 1; }

git fetch origin
git merge --no-edit origin/develop || true
git push origin "$BRANCH"
