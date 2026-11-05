#!/usr/bin/env sh
set -eu
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
cd frontend && npm install

