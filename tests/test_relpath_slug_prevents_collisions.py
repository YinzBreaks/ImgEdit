import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

from src.cli import run_pipeline_batch


def _write_schema(tmp_path: Path) -> None:
    repo_schema = Path.cwd() / "schemas" / "preset.schema.json"
    schema_dst = tmp_path / "schemas" / "preset.schema.json"
    schema_dst.parent.mkdir(parents=True, exist_ok=True)
    schema_dst.write_text(repo_schema.read_text(encoding="utf-8"), encoding="utf-8")


def _write_preset(path: Path) -> None:
    preset: dict[str, object] = {
        "name": "slug_collision_test",
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


def _write_image(path: Path, value: int) -> None:
    arr = np.zeros((24, 24, 3), dtype=np.uint8)
    arr[..., 0] = value
    Image.fromarray(arr, mode="RGB").save(path, format="PNG")


def test_relpath_slug_prevents_collisions(tmp_path: Path) -> None:
    _write_schema(tmp_path)

    input_dir = tmp_path / "in"
    (input_dir / "subA").mkdir(parents=True, exist_ok=True)
    (input_dir / "subB").mkdir(parents=True, exist_ok=True)

    _write_image(input_dir / "subA" / "item.png", 50)
    _write_image(input_dir / "subB" / "item.png", 150)

    preset_file = tmp_path / "preset.json"
    _write_preset(preset_file)

    out_dir = tmp_path / "out"
    reports_dir = tmp_path / "reports"

    discovered = sorted(
        [p for p in input_dir.rglob("*.png")],
        key=lambda p: p.as_posix(),
    )

    cwd_before = Path.cwd()
    try:
        os.chdir(tmp_path)
        run_pipeline_batch(
            preset_path=preset_file,
            input_paths=discovered,
            input_dir=input_dir,
            recursive=True,
            include_ext="png,jpg,jpeg",
            glob_pattern="*.png",
            outdir=out_dir,
            reports_dir=reports_dir,
            on_error="stop",
            dry_run=False,
            max_files=None,
        )
    finally:
        os.chdir(cwd_before)

    outputs = sorted(out_dir.glob("*.png"), key=lambda p: p.name)
    output_names = [path.name for path in outputs]

    expected_output_names = {
        "suba__item_slug_collision_test_v001.png",
        "subb__item_slug_collision_test_v001.png",
    }

    assert set(output_names) == expected_output_names

    # Verify that the outputs are not only named correctly but also correspond
    # to distinct input images with different red-channel intensities.
    suba_paths = [p for p in outputs if p.name == "suba__item_slug_collision_test_v001.png"]
    subb_paths = [p for p in outputs if p.name == "subb__item_slug_collision_test_v001.png"]
    assert len(suba_paths) == 1
    assert len(subb_paths) == 1

    suba_arr = np.array(Image.open(suba_paths[0]))
    subb_arr = np.array(Image.open(subb_paths[0]))

    suba_red_mean = suba_arr[..., 0].mean()
    subb_red_mean = subb_arr[..., 0].mean()

    # Input images were written with red-channel values 50 (subA) and 150 (subB).
    # Check that the corresponding outputs preserve this ordering.
    assert suba_red_mean < 100
    assert subb_red_mean > 100
