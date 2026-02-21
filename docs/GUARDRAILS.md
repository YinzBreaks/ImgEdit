# Guardrails

## Why Guardrails Exist

Commercial workflows require repeatability, auditability, and strict control over creative drift. These guardrails ensure edits remain enhancements, not redesigns.

## Hard Guardrails

- Strict preset schema; unknown fields fail validation.
- No geometry changes unless explicitly enabled in preset.
- Clipping threshold gate must pass.
- Translation drift gate must pass when composition is expected unchanged.
- Deterministic encoder settings and parameterized operations only.
- No output overwrite; version-only file naming.

## Drift Prevention Checklist

- [ ] Preset changed intentionally and reviewed.
- [ ] Preset validates with zero schema errors.
- [ ] `safety.no_geometry_change` is true unless geometry is explicitly required.
- [ ] `safety.identical_composition_expected` aligns with project intent.
- [ ] Clipping threshold is conservative and passed.
- [ ] Report and manifest include hashes + versions.
- [ ] Determinism test remains green.
