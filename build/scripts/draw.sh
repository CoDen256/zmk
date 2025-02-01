#!/usr/bin/env bash

echo "Running keymap drawer: $(keymap -v): $(which keymap)"
python /config/draw/drawer.py $(which keymap)