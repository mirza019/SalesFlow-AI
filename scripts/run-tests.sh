#!/usr/bin/env sh
set -eu
pytest backend/tests
cd frontend && npm test -- --run

