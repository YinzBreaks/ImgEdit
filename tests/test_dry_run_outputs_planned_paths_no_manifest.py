import json
import os
from pathlib import Path

from src.cli import run_pipeline_batch


def _write_schema(tmp_path: Path) -> None:
    repo_schema = Path.cwd() / "schemas" / "preset.schema.json"
    schema_dst = tmp_path / "schemas" / "preset.schema.json"
    schema_dst.parent.mkdir(parents=True, exist_ok=True)
    schema_dst.write_text(repo_schema.read_text(encoding="utf-8"), encoding="utf-8")


def _write_valid_preset(path: Path) -> None:
    preset: dict[str, object] = {
        "name": "dry_run_test",
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
            "include_relpath_slug": True,
        },
    }
    path.write_text(json.dumps(preset, indent=2), encoding="utf-8")


def _write_invalid_preset(path: Path) -> None:
    data = json.loads((path.parent / "preset_valid.json").read_text(encoding="utf-8"))
    data["tone"]["unknown_field"] = 1
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_dry_run_outputs_planned_paths_no_manifest(tmp_path: Path) -> None:
    _write_schema(tmp_path)

    input_dir = tmp_path / "in"
    input_dir.mkdir(parents=True, exist_ok=True)
    # Use a non-image placeholder file: in dry-run mode no pixel data is read, only
    # input discovery and output planning are exercised, so the file contents are irrelevant.
    (input_dir / "demo.png").write_text("placeholder-not-image", encoding="utf-8")

    valid_preset = tmp_path / "preset_valid.json"
    _write_valid_preset(valid_preset)

    out_dir = tmp_path / "out"
    reports_dir = tmp_path / "reports"

    discovered: list[Path] = [input_dir / "demo.png"]

    cwd_before = Path.cwd()
    try:
        os.chdir(tmp_path)
        result = run_pipeline_batch(
            preset_path=valid_preset,
            input_paths=discovered,
            input_dir=input_dir,
            recursive=True,
            include_ext="png,jpg,jpeg",
            glob_pattern="*.png",
            outdir=out_dir,
            reports_dir=reports_dir,
            on_error="stop",
            dry_run=True,
            max_files=None,
        )
    finally:
        os.chdir(cwd_before)

    assert list(out_dir.glob("*")) == []
    assert not (reports_dir / "manifest.json").exists()

    summary_text = Path(result["summary_path"]).read_text(encoding="utf-8")
    assert "mode: `dry-run`" in summary_text
    assert "demo" in summary_text
    assert "_v001.png" in summary_text

    invalid_preset = tmp_path / "preset_invalid.json"
    _write_invalid_preset(invalid_preset)

    cwd_before = Path.cwd()
    try:
        os.chdir(tmp_path)
        try:
            run_pipeline_batch(
                preset_path=invalid_preset,
                input_paths=discovered,
                input_dir=input_dir,
                recursive=True,
                include_ext="png,jpg,jpeg",
                glob_pattern="*.png",
                outdir=out_dir,
                reports_dir=reports_dir,
                on_error="stop",
                dry_run=True,
                max_files=None,
            )
            assert False, "Expected schema validation failure in dry-run"
        except ValueError as exc:
            assert "Preset validation failed" in str(exc)
    finally:
        os.chdir(cwd_before)
