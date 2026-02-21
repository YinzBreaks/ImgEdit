# Acceptance Criteria (Must Pass)

## Contract and Safety

- [ ] Changes remain enhancement-only with no forbidden operations.
- [ ] Preset schema rejects unknown fields.
- [ ] Geometry protections are enforced for `no_geometry_change` workflows.

## Determinism and Auditability

- [ ] Repeat runs on identical inputs produce identical output pixels.
- [ ] Manifest contains input/preset/output hashes and settings snapshot.
- [ ] Per-image reports are generated with versions and QA outcomes.

## Export and Versioning

- [ ] Outputs are versioned (`_v001`, `_v002`, ...).
- [ ] Existing outputs are never overwritten.

## Test Alignment (Current Repo)

- [ ] `tests/test_schema_rejects_unknown_fields.py` passes.
- [ ] `tests/test_no_geometry_change_pixel_diff_gate.py` passes.
- [ ] `tests/test_manifest_hashes_present.py` passes.
- [ ] `tests/test_determinism_same_input_same_output_pixels.py` passes.
