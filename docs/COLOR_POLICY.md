# Color Policy

## Working Space

- Pipeline processing runs in RGB.
- Source is loaded with profile awareness; ICC profile is preserved when available.
- Do not convert to CMYK unless explicitly requested in a dedicated output requirement.

## Export Policy

- PNG master retained by default for archival/quality stability.
- JPEG web derivatives allowed via preset with fixed quality.
- ICC profile embedding is controlled by `export.embed_profile`.

## Print Notes (Canvas / Matte)

- Use high-resolution RGB master exports for print handoff.
- Keep enhancement subtle to avoid print clipping surprises.
- Coordinate final print-space conversion with print vendor requirements.
