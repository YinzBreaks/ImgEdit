# Editing Contract: Enhance Only / No Drift

## Purpose

This pipeline exists to produce commercially viable image enhancements without changing creative intent.

## Non-Negotiable Rules

1. Enhance-only operations are allowed (tone, color balance, subtle denoise/sharpen, explicit resize/crop when requested).
2. Content edits are forbidden unless explicitly requested in a future contract revision.
3. Geometry must remain unchanged when a preset marks `safety.no_geometry_change: true`.
4. Every operation must come from preset JSON, be schema-valid, and be logged in reports/manifest.
5. Pipeline behavior must be deterministic for identical inputs + preset + runtime stack.

## Explicitly Forbidden Actions

- Generative fill or synthesis of new scene content.
- Object insertion/removal, background replacement, compositing, inpainting.
- Unapproved reframing, perspective warps, rotations, or translations.
- Manual one-off edits that bypass preset and logs.
- Silent overwrite of existing outputs.

## How to Request Changes Properly

1. Propose a preset update in JSON.
2. Validate against `schemas/preset.schema.json`.
3. Run QA checklist and tests.
4. Review generated report and manifest entry.
5. Approve change only if guardrails remain intact.

## Breach Handling

If any guardrail fails:

- Stop export.
- Record failure in report notes.
- Fix preset or code and rerun deterministically.
