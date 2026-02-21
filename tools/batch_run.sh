#!/usr/bin/env bash
set -euo pipefail

PRESET="${1:-presets/ebay_square.json}"
INPUT_DIR="${2:-in}"
GLOB_PATTERN="${3:-*.png}"
OUT_DIR="${4:-out}"
REPORTS_DIR="${5:-reports}"

python -m src.cli --preset "$PRESET" --input-dir "$INPUT_DIR" --glob "$GLOB_PATTERN" --outdir "$OUT_DIR" --reports-dir "$REPORTS_DIR"
