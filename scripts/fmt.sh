#!/usr/bin/env bash
set -euo pipefail
cd apps/api
uv run ruff format .
uv run ruff check . --fix
