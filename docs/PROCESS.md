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

## Deliverables Per Run

- Versioned output files in `out/`.
- Per-image markdown report in `reports/`.
- Manifest append in `reports/manifest.json`.

## Failure Behavior

- Invalid preset: run aborts with non-zero exit.
- QA gate failure: run aborts with non-zero exit.
- Existing filename collision: new `_vNNN` output generated automatically.
