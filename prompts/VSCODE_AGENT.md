# VS Code Agent Starter (Paste-in Prompt)

Use this starter when beginning any session in this repository.

---

Read these files first and confirm compliance before editing:

1. `rules/EDITING_CONTRACT.md`
2. `rules/DRIFT_PREVENTION.md`
3. `rules/ACCEPTANCE_CRITERIA.md`
4. `rules/ENFORCEMENT_MATRIX.md`
5. `prompts/SYSTEM.md`
6. `prompts/FAILURE_PROTOCOL.md`

Operating mode for this session:

- Enhance-Only / No Drift is mandatory.
- Preset-first, deterministic, fully auditable changes only.
- Unknown fields fail schema; no silent behavior changes.
- Versioned outputs only; no overwrite behavior.
- Ask exactly one minimal clarification question and stop if direction is ambiguous.

Implementation policy:

- Use Codex 5.3 for all code/config/test edits.
- Keep deltas minimal and explicit.
- Do not change pipeline behavior unless explicitly requested.
- After edits, provide touched-file full contents or full diffs.

Acknowledge with: "Rules loaded and enforced."

---
