# Failure Protocol (Minimal Clarification)

When a request is unclear, incomplete, or potentially contract-breaking:

1. Ask **exactly one** minimal clarification question.
2. Stop work after asking the question.
3. Do not infer risky intent.
4. Do not implement speculative changes.

## Minimal Question Pattern

"Please confirm one point so I can proceed safely: <single missing decision>?"

## Examples

- "Please confirm one point so I can proceed safely: should geometry remain unchanged (`no_geometry_change=true`) for this revision?"
- "Please confirm one point so I can proceed safely: is this request enhancement-only, with no object/content edits?"

## Resume Rule

After user clarification, continue with smallest valid delta consistent with all rules in `rules/`.
