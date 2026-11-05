#!/usr/bin/env sh
set -eu
python -m database.synthetic_data.generate_all "$@"

