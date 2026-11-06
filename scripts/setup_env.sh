#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null; then
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi
case "${1:-}" in
  "") uv sync --locked ;;
  --gpu) uv sync --locked --extra gpu ;;
  *) echo "Usage: ./scripts/setup_env.sh [--gpu]" >&2; exit 2 ;;
esac
