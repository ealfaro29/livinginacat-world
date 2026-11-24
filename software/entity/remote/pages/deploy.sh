#!/bin/sh
set -eu

pages_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
brand_dir="$pages_dir/../../src/physiclaw/static/entity"
stage_dir=$(mktemp -d "${TMPDIR:-/tmp}/entity-pages.XXXXXXXX")
trap 'rm -rf -- "$stage_dir"' EXIT
cp -R "$pages_dir/site" "$stage_dir/site"
cp "$pages_dir/wrangler.toml" "$stage_dir/wrangler.toml"
cp "$brand_dir/sentient.svg" "$brand_dir/space-grotesk.ttf" "$brand_dir/OFL.txt" "$stage_dir/site/ui/"
cd "$stage_dir"
"${WRANGLER:-wrangler}" pages deploy site --project-name entity-alfonsito --branch main
