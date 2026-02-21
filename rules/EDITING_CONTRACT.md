# Editing Contract (Ironclad)

## Contract Scope

This repository processes images under a strict **Enhance-Only / No Drift** policy.

## Forbidden Actions (Never Allowed)

1. Generative fill, inpainting, synthesis, or AI hallucination.
2. Object insertion/removal, background replacement, scene recomposition.
3. Unrequested geometry changes (crop, resize, warp, rotate, translate).
4. Manual, unlogged edits outside preset-driven pipeline behavior.
5. Silent overwrite of existing outputs.
6. Introducing non-deterministic behavior without explicit approval.

## Allowed Actions (With Explicit Direction)

- Subtle parameterized tone/color/detail enhancement.
- Crop/resize only when explicitly enabled in preset.
- Export format and quality adjustments through preset fields.

## Explicit Direction Format (Required)

Any behavior-changing request should include:

- Preset target (`presets/<name>.json`)
- Exact field deltas (`from -> to`)
- Intended output channel (IG/eBay/print)
- QA expectation (`no_geometry_change`, clipping threshold, translation tolerance)

Template:

```text
Preset: presets/<file>.json
Changes:
- tone.exposure_ev: <old> -> <new>
- color.vibrance: <old> -> <new>
Constraints:
- no_geometry_change: <true|false>
- max_channel_clip_pct: <value>
Reason: <commercial intent>
```
