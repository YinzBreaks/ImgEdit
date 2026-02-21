# QA Checklist

## Automated Gates (Must Pass)

- [ ] Preset schema validation passes with no unknown fields.
- [ ] Geometry policy passes (`no_geometry_change` enforced when set).
- [ ] Clipping gate passes (`after clipped % <= max_channel_clip_pct`).
- [ ] Translation drift gate passes when identical composition is expected.
- [ ] Determinism test passes for repeated runs.

## Report and Manifest Audit

- [ ] Report exists for each output.
- [ ] Report includes input hash, preset hash, versions, QA notes.
- [ ] Manifest includes input/output hashes and settings snapshot.
- [ ] Output names are versioned (`_vNNN`).

## Manual Review

- [ ] No unexpected framing change.
- [ ] No obvious clipping artifacts.
- [ ] Enhancement remains subtle and commercially viable.
- [ ] Colors remain natural for channel intent (IG/eBay/print).

## Suggested Command Sequence

```bash
pytest
python -m src.cli --preset presets/instagram_4x5.json --input in/sample.png --outdir out --reports-dir reports
```
