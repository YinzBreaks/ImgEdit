# Revision-Only Template (Delta Discipline)

Use this template for all subsequent change requests.

## Request Envelope

- Objective:
- Scope (files/modules):
- Out of scope:
- Behavior change allowed? (yes/no):
- Preset/schema impact:
- Required tests:

## Change Rules

1. Modify only files required to satisfy the request.
2. Preserve existing public behavior unless behavior change is explicitly allowed.
3. Keep naming/versioning/determinism guarantees intact.
4. Update docs only where directly affected.

## Output Format

- Summary of change intent (2-4 lines).
- Full diff or full content for touched files.
- Validation evidence (commands + results).
- Any unresolved risk or follow-up action.
