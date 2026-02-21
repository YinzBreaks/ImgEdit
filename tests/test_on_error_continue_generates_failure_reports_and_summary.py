import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

from src.cli import _discover_inputs, run_pipeline_batch


def _write_schema(tmp_path: Path) -> None:
    repo_schema = Path.cwd() / "schemas" / "preset.schema.json"
    schema_dst = tmp_path / "schemas" / "preset.schema.json"
    schema_dst.parent.mkdir(parents=True, exist_ok=True)
    schema_dst.write_text(repo_schema.read_text(encoding="utf-8"), encoding="utf-8")


def _write_preset(path: Path) -> None:
    preset = {
        "name": "continue_test",
        "io": {"preserve_metadata": True, "exif_transpose": False},
        "tone": {"exposure_ev": 0.0, "contrast": 0.0, "black_point": 0.0, "white_point": 0.0},
        "color": {"saturation": 0.0, "vibrance": 0.0, "wb_mode": "none"},
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
            "include_relpath_slug": False,
        },
    }
    path.write_text(json.dumps(preset, indent=2), encoding="utf-8")


def _write_valid_image(path: Path) -> None:
    arr = np.zeros((32, 32, 3), dtype=np.uint8)
    arr[..., 1] = 128
    Image.fromarray(arr, mode="RGB").save(path, format="PNG")


def test_on_error_continue_generates_failure_reports_and_summary(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    _write_schema(tmp_path)

    input_dir = tmp_path / "in"
    input_dir.mkdir(parents=True, exist_ok=True)
    _write_valid_image(input_dir / "ok.png")
    (input_dir / "bad.png").write_text("not-a-real-image", encoding="utf-8")

    preset_file = tmp_path / "preset.json"
    _write_preset(preset_file)

    out_dir = tmp_path / "out"
    reports_dir = tmp_path / "reports"

    discovered = _discover_inputs(
        input_dir=input_dir,
        glob_pattern="*.png",
        recursive=False,
        include_ext_csv="png,jpg,jpeg",
        max_files=None,
    )

    cwd_before = Path.cwd()
    try:
        os.chdir(tmp_path)
        result = run_pipeline_batch(
            preset_path=preset_file,
            input_paths=discovered,
            input_dir=input_dir,
            recursive=False,
            include_ext="png,jpg,jpeg",
            glob_pattern="*.png",
            outdir=out_dir,
            reports_dir=reports_dir,
            on_error="continue",
            dry_run=False,
            max_files=None,
        )
    finally:
        os.chdir(cwd_before)

    assert len(result["entries"]) == 1
    assert len(result["failures"]) == 1

    failure_report = Path(result["failures"][0]["failure_report"])
    assert failure_report.exists()

    summary_text = Path(result["summary_path"]).read_text(encoding="utf-8")
    assert "failed: `1`" in summary_text
    assert "bad.png" in summary_text

    outputs = list(out_dir.glob("*.png"))
    assert len(outputs) == 1

    manifest = json.loads((reports_dir / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest.get("entries", [])) == 1
