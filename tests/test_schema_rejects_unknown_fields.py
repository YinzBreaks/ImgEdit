from pathlib import Path

import pytest

from src.pipeline.validate import load_schema, validate_preset


def test_schema_rejects_unknown_fields() -> None:
    schema = load_schema(Path("schemas/preset.schema.json"))
    preset = {
        "name": "invalid",
        "io": {"preserve_metadata": True, "exif_transpose": False},
        "tone": {
            "exposure_ev": 0.0,
            "contrast": 0.0,
            "black_point": 0.0,
            "white_point": 0.0,
            "unknown": 1
        },
        "color": {"saturation": 0.0, "vibrance": 0.0, "wb_mode": "none"},
        "detail": {"denoise_strength": 0.0, "sharpen_amount": 0.0, "sharpen_radius": 1.0},
        "geometry": {
            "enabled": False,
            "crop": {"enabled": False, "x": 0, "y": 0, "width": 1, "height": 1},
            "resize": {"enabled": False, "width": 1, "height": 1, "resample": "lanczos"}
        },
        "safety": {
            "max_channel_clip_pct": 5.0,
            "clip_eval_mode": "any_channel",
            "clip_black_level": 0,
            "clip_white_level": 255,
            "no_geometry_change": True,
            "identical_composition_expected": True,
            "max_translation_pixels": 0.0,
            "pixel_diff_gate": False,
            "max_mae": 0.0,
            "max_diff_pixels_pct": 0.0
        },
        "export": {
            "keep_png_master": True,
            "web_enabled": False,
            "web_format": "jpeg",
            "web_quality": 90,
            "embed_profile": True
        }
    }

    with pytest.raises(ValueError):
        validate_preset(preset, schema)
