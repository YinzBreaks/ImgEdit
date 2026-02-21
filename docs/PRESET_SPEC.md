# Preset Spec

All fields are mandatory and validated by `schemas/preset.schema.json`.

## Top-Level Fields

- `name` (string): preset identifier used in filenames/reports.
- `io.preserve_metadata` (bool): preserve source metadata where possible.
- `io.exif_transpose` (bool): apply EXIF orientation normalization on load (default runtime behavior is false unless preset enables it).
- `tone` (object): exposure/contrast/black/white controls.
- `color` (object): saturation/vibrance/white-balance mode.
- `detail` (object): denoise and sharpen controls.
- `geometry` (object): explicit crop/resize controls.
- `safety` (object): QA thresholds and composition policy.
- `export` (object): PNG master + optional web JPEG controls.

## Tone Safe Ranges

- `exposure_ev`: `[-0.5, 0.5]`
- `contrast`: `[-0.3, 0.3]`
- `black_point`: `[0.0, 0.2]`
- `white_point`: `[0.0, 0.2]`

## Color Safe Ranges

- `saturation`: `[-0.3, 0.3]`
- `vibrance`: `[-0.3, 0.3]`
- `wb_mode`: `none | auto | daylight | tungsten`

## Detail Safe Ranges

- `denoise_strength`: `[0.0, 1.0]`
- `sharpen_amount`: `[0.0, 2.0]`
- `sharpen_radius`: `[0.1, 3.0]`

## Geometry Rules

- `geometry.enabled` must be `true` to allow crop/resize.
- `crop.enabled` and `resize.enabled` are independent toggles.
- If `safety.no_geometry_change: true`, any enabled geometry operation fails.

## Safety Fields

- `max_channel_clip_pct`: maximum allowed clipped channel percentage.
- `clip_eval_mode`: clipping evaluation mode: `any_channel | luma_only | per_channel`.
- `clip_black_level`: integer black clipping threshold `[0..5]`.
- `clip_white_level`: integer white clipping threshold `[250..255]`.
- `no_geometry_change`: enforce no resize/crop.
- `identical_composition_expected`: activates translation drift check.
- `max_translation_pixels`: max allowed shift in phase-correlation estimate.
- `pixel_diff_gate`: enables true pixel-difference gate.
- `max_mae`: max mean absolute grayscale error for pixel diff gate `[0..10]`.
- `max_diff_pixels_pct`: max percentage of changed pixels for pixel diff gate `[0..100]`.

## Export Fields

- `keep_png_master`: keep deterministic PNG master.
- `web_enabled`: produce web derivative.
- `web_format`: `jpeg`/`jpg`.
- `web_quality`: JPEG quality `1..100`.
- `embed_profile`: embed ICC profile if available.
