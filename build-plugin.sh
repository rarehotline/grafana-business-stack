#!/usr/bin/env bash
# Usage: ./build-plugin.sh <github-owner/repo> <tag> [name]
# Clones the repo at <tag>, builds it, and packs dist/ into out/<plugin-id>-<version>.zip
# in the layout Grafana expects (single top-level <plugin-id>/ directory).
set -euo pipefail
repo=$1 tag=$2 name=${3:-$(basename "$1")}
root=$(cd "$(dirname "$0")" && pwd)
src=$root/src/$name
mkdir -p "$root/out" "$root/src"

[ -d "$src" ] || git clone -q --depth 1 --branch "$tag" "https://github.com/$repo" "$src"
cd "$src"
# Pin Node to what the plugins' engines allow (system node is newer than any of them support).
run() { mise exec node@24 -- "$@"; }
if [ -f yarn.lock ]; then
  export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
  run corepack yarn install --immutable
  run corepack yarn build
else
  # Newer npm refuses git deps (EALLOWGIT); some plugins pin a grafana/react-data-grid fork by commit.
  run npm ci --allow-git=all --no-audit --no-fund
  run npm run build
fi
# Datasources with a Go backend (clickhouse, infinity) ship per-arch binaries inside dist/.
if [ -f Magefile.go ]; then
  go run github.com/magefile/mage -v build:linux
fi

id=$(run node -p 'require("./dist/plugin.json").id')
ver=$(run node -p 'require("./dist/plugin.json").info.version')
case $ver in *%*) echo "unsubstituted version in dist/plugin.json: $ver" >&2; exit 1;; esac

stage=$(mktemp -d); trap 'rm -rf "$stage"' EXIT
cp -r dist "$stage/$id"
(cd "$stage" && zip -qr "$root/out/$id-$ver.zip" "$id")
echo "built $root/out/$id-$ver.zip"
