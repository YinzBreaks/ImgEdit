# Enforcement Matrix

| Rule | Enforcement in Code | Enforcement in Tests | Artifact Evidence |
|---|---|---|---|
| Unknown preset fields must fail | `src/pipeline/validate.py` (`Draft202012Validator`, `validate_preset`) + `schemas/preset.schema.json` (`additionalProperties: false`) | `tests/test_schema_rejects_unknown_fields.py` | CLI non-zero on invalid preset; validation error output |
| No geometry change when prohibited | `src/pipeline/geometry.py` (`enforce_no_geometry_change_policy`, `assert_geometry_unchanged`) and `src/cli.py` safety checks | `tests/test_no_geometry_change_pixel_diff_gate.py` | QA notes in per-image report |
| Composition drift gate for translation | `src/pipeline/geometry.py` (`estimate_translation_pixels`) invoked by `src/cli.py` when composition is expected identical | Covered by safety path logic in pipeline run; geometry guard test present | Report gate line: translation pass/fail |
| Deterministic output pixels | Stable processing path in `src/cli.py` and stable encoders in `src/pipeline/io.py` + versioned export path in `src/pipeline/export.py` | `tests/test_determinism_same_input_same_output_pixels.py` | Repeat-run pixel equality |
| Hashes must be present in manifest | `src/cli.py` computes hashes, `src/pipeline/manifest.py` persists | `tests/test_manifest_hashes_present.py` | `reports/manifest.json` entries |
| No overwrite; versioned naming only | `src/pipeline/export.py` (`build_versioned_paths`) | Covered indirectly by determinism run creating multiple versions | Output filenames with `_vNNN` |
| Report per output with versions and metrics | `src/pipeline/report.py` + `src/cli.py` payload assembly | Exercised through pipeline tests | Markdown report in `reports/` |
