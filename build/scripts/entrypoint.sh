#!/usr/bin/env bash
set -euo pipefail

echo "hello"
/build/scripts/draw.sh
exit 1
: "${BRANCH:=main}"

echo "Checking out $BRANCH from moergo-sc/zmk" >&2
cd /src
git fetch origin
git checkout -q --detach "$BRANCH"

echo 'Building Glove80 firmware' >&2
cd /config
nix-build ./config --arg firmware 'import /src/default.nix {}' -j2 -o /tmp/combined --show-trace
install -o "$UID" -g "$GID" /tmp/combined/glove80.uf2 ./glove80.uf2

