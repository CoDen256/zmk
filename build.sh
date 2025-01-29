#!/usr/bin/env bash

set -euo pipefail
IMAGE=coden256/glove80-zmk-config-linux
BRANCH="${1:-main}"

docker run --rm -v "$PWD:/config" -e UID="$(id -u)" -e GID="$(id -g)" -e BRANCH="$BRANCH" "$IMAGE"