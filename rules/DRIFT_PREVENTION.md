# Drift Prevention Rules

## Preset-First Requirement

- All behavior must be controlled by preset JSON validated against `schemas/preset.schema.json`.
- Unknown fields are invalid and must fail before processing.

## Determinism Requirement

- Same input + same preset + same environment must produce identical pixel arrays.
- Stable export settings must be used (fixed PNG/JPEG encoder parameters).

## Hashing and Traceability

- Record input SHA256, preset SHA256, and output SHA256.
- Include versions (Python, Pillow, NumPy, jsonschema) in reports and manifest.
- Keep run metadata append-only via manifest entries.

## Versioned Output Policy

- Never overwrite outputs.
- Use `_vNNN` suffix incrementing on collisions.

## Geometry/Composition Protection

- If `safety.no_geometry_change` is true, any geometry operation must fail.
- If `safety.identical_composition_expected` is true, translation drift gate must pass.
