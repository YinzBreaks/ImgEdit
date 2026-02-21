# Process

## End-to-End Workflow

1. Intake source images into `in/`.
2. Select or author a preset in `presets/`.
3. Validate preset against `schemas/preset.schema.json` (including `io.exif_transpose` and safety gates).
4. Run pipeline via `python -m src.cli`.
5. Execute QA gates (automatic) and optional manual review.
6. Deliver outputs from `out/` with report artifacts from `reports/`.

## Load and QA Notes

- EXIF transpose is only applied when `io.exif_transpose=true`.
- Clipping gate uses configurable thresholds (`clip_black_level`, `clip_white_level`) and evaluation mode (`any_channel`, `luma_only`, or `per_channel`).
- Translation gate evaluates composition shift when `identical_composition_expected=true`.
- Pixel diff gate is optional and enabled with `safety.pixel_diff_gate=true`.

## Execution Patterns

Single image:

```bash
python -m src.cli --preset presets/instagram_4x5.json --input in/my.png --outdir out --reports-dir reports
```

Batch mode:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --glob "*.png" --outdir out --reports-dir reports
```

Recursive batch mode:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --recursive --include-ext "png,jpg,jpeg" --outdir out --reports-dir reports
```

Dry-run audit mode:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --recursive --dry-run --outdir out --reports-dir reports
```

Continue-on-error mode:

```bash
python -m src.cli --preset presets/ebay_square.json --input-dir in --recursive --on-error continue --outdir out --reports-dir reports
```

Deterministic discovery rules:

- With `--input-dir --recursive`, discovery filters by `--include-ext` regardless of `--glob`.
- Inputs are sorted by normalized relative POSIX path from input directory.
- `--max-files` limits the sorted input list.

## Deliverables Per Run

- Versioned output files in `out/`.
- Per-image markdown report in `reports/`.
- Manifest append in `reports/manifest.json`.
- Batch summary report in `reports/batch_<timestamp>.md`.
- On `--on-error continue`, per-image failure reports in `reports/*_FAIL.md`.

## Dry-Run Behavior

- Validates preset schema and fails with non-zero exit on invalid preset.
- Discovers and orders inputs deterministically.
- Computes planned versioned output paths with the same version-selection logic as real runs.
- Does not read/process image pixels.
- Does not export output files.
- Does not append `reports/manifest.json`.
- Writes `reports/batch_<timestamp>.md` with planned outputs.

## Failure Behavior

- Invalid preset: run aborts with non-zero exit.
- QA gate failure with `--on-error stop`: run aborts with non-zero exit.
- QA gate failure with `--on-error continue`: failure report is written and batch continues.
- Existing filename collision: new `_vNNN` output generated automatically.
