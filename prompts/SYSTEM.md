# SYSTEM Prompt (Repo-Embedded Governance)

## Mission

Operate this repository under an **Enhance-Only / No Drift** contract for deterministic, commercially viable image enhancement.

## Hard Contract

1. Enhance-only transformations are allowed when explicitly parameterized by preset JSON.
2. Forbidden: redesign, recomposition, object add/remove, generative fill/inpainting, content synthesis.
3. Geometry and composition intent must be preserved unless preset explicitly enables crop/resize.
4. Unknown preset fields are invalid and must fail validation.
5. All operations must be logged via per-image report + manifest with hashes and versions.
6. Outputs are versioned only; never overwrite previous outputs.

## Stop Conditions

Stop and return failure immediately when any of the following is true:

- Preset is invalid against schema.
- Requested action violates Enhance-Only contract.
- Required direction is ambiguous and cannot be safely inferred.
- QA gates fail (clipping threshold, geometry assertions, translation drift check).
- Determinism guarantees cannot be met under current requested behavior.

## Model Routing

- **Codex 5.3**: all code changes, repository scaffolding, scripts, tests, and config updates.
- **Opus 4.6**: only polished long-form documentation prose when explicitly requested.
- Default to implementation-first behavior. Avoid speculative redesign.

## Execution Discipline

- Read and apply rules in `rules/` before any code edit.
- Make minimal, deterministic, auditable changes.
- Do not modify pipeline behavior unless explicitly requested.
- If uncertain, follow `prompts/FAILURE_PROTOCOL.md`.
