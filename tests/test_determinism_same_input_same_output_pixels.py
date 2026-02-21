import json
from pathlib import Path

import numpy as np
from PIL import Image

from src.cli import run_pipeline


def _write_test_image(path: Path) -> None:
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[..., 0] = np.tile(np.arange(64, dtype=np.uint8), (64, 1))
    arr[..., 1] = 120
    arr[..., 2] = 200
    Image.fromarray(arr, mode="RGB").save(path, format="PNG")


def _write_preset(path: Path) -> None:
    preset = {
        "name": "determinism_test",
        "io": {"preserve_metadata": True, "exif_transpose": False},
        "tone": {
            "exposure_ev": 0.05,
            "contrast": 0.05,
            "black_point": 0.0,
            "white_point": 0.0,
        },
        "color": {"saturation": 0.03, "vibrance": 0.02, "wb_mode": "none"},
        "detail": {"denoise_strength": 0.0, "sharpen_amount": 0.0, "sharpen_radius": 1.0},
        "geometry": {
            "enabled": False,
            "crop": {"enabled": False, "x": 0, "y": 0, "width": 1, "height": 1},
            "resize": {"enabled": False, "width": 1, "height": 1, "resample": "lanczos"},
        },
        "safety": {
            "max_channel_clip_pct": 100.0,
            "clip_eval_mode": "any_channel",
            "clip_black_level": 0,
            "clip_white_level": 255,
            "no_geometry_change": True,
            "identical_composition_expected": True,
            "max_translation_pixels": 0.0,
            "pixel_diff_gate": False,
            "max_mae": 0.0,
            "max_diff_pixels_pct": 0.0,
        },
        "export": {
            "keep_png_master": True,
            "web_enabled": False,
            "web_format": "jpeg",
            "web_quality": 90,
            "embed_profile": True,
        },
    }
    path.write_text(json.dumps(preset, indent=2), encoding="utf-8")


def test_determinism_same_input_same_output_pixels(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    schema_src = repo_root / "schemas" / "preset.schema.json"
    schema_dst = tmp_path / "schemas" / "preset.schema.json"
    schema_dst.parent.mkdir(parents=True, exist_ok=True)
    schema_dst.write_text(schema_src.read_text(encoding="utf-8"), encoding="utf-8")

    input_file = tmp_path / "in.png"
    _write_test_image(input_file)

    preset_file = tmp_path / "preset.json"
    _write_preset(preset_file)

    out_dir = tmp_path / "out"
    reports_dir = tmp_path / "reports"

    cwd_before = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)
        run_pipeline(preset_file, [input_file], out_dir, reports_dir)
        run_pipeline(preset_file, [input_file], out_dir, reports_dir)
    finally:
        os.chdir(cwd_before)

    outputs = sorted(out_dir.glob("*.png"))
    assert len(outputs) == 2

    a = np.asarray(Image.open(outputs[0]).convert("RGB"), dtype=np.uint8)
    b = np.asarray(Image.open(outputs[1]).convert("RGB"), dtype=np.uint8)
    assert np.array_equal(a, b)
