#!/usr/bin/env bash

docker run --rm -it -v "$PWD:/config" -v "$PWD/build:/build" -e UID="$(id -u)" -e GID="$(id -g)" -e BRANCH=main --entrypoint /bin/bash coden256/glove80-zmk-config-linux