# Runbook

## Common Commands

Create environment and install dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

Single image run:

```bash
python -m src.cli --preset presets/instagram_4x5.json --input in/demo.png --outdir out --reports-dir reports
```

Batch run:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --glob "*.png" --outdir out --reports-dir reports
```

Recursive batch run:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --recursive --outdir out --reports-dir reports
```

Continue-on-error batch run:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --recursive --on-error continue --outdir out --reports-dir reports
```

Dry-run audit:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --recursive --dry-run --outdir out --reports-dir reports
```

Optional file cap:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --recursive --max-files 100 --outdir out --reports-dir reports
```

Tests:

```bash
./.venv/Scripts/python.exe -m pytest -q
```

If `.venv` is already activated, `pytest -q` is equivalent.

## Troubleshooting

- Preset validation errors: inspect field path in CLI output; remove unknown keys.
- Geometry policy error: disable geometry or set `safety.no_geometry_change` to `false` intentionally.
- Clipping gate failure: reduce exposure/contrast, adjust points conservatively.
- Translation gate failure: investigate unintended transform/shift behavior.
- Pixel diff gate failure: relax `max_mae`/`max_diff_pixels_pct` only when explicitly justified.
- Recursive discovery misses files: check `--include-ext` list (defaults to `png,jpg,jpeg`).
- Colliding names across subfolders: set `export.include_relpath_slug=true`.
- Need audit without mutation: use `--dry-run`; review `reports/batch_<timestamp>.md`.

## Adding a New Preset Safely

1. Copy an existing preset.
2. Change only required fields.
3. Validate and run tests.
4. Run sample input and inspect report + manifest.
5. Commit only after guardrail pass.

## Reading Reports

Each report captures input hash, preset hash, versions, before/after metrics, and QA gate outcomes. Manifest provides machine-readable batch traceability.
