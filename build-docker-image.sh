#!/usr/bin/env bash

set -euo pipefail

IMAGE=coden256/glove80-zmk-config-linux

docker build -t "$IMAGE" .