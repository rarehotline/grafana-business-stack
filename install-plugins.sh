#!/usr/bin/env bash
# Unpack every zip from out/ into plugins/ (replaces any previous version of that plugin).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p plugins
for z in out/*.zip; do
  id=$(unzip -Z1 "$z" | sed -n 1p | cut -d/ -f1)
  rm -rf "plugins/$id"
  unzip -q "$z" -d plugins
  echo "installed $id from $z"
done
