#!/usr/bin/env sh
set -eu
profile="${1:-full}"
python -m database.synthetic_data.generate_all --profile "$profile" --seed 42 --format both --validate --overwrite

