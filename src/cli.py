from __future__ import annotations

import argparse
import datetime as dt
import glob
import importlib.metadata
import platform
from pathlib import Path

import numpy as np

from src.pipeline.color import apply_color
from src.pipeline.detail import apply_detail
from src.pipeline.export import build_versioned_paths, export_images
from src.pipeline.geometry import (
    apply_geometry,
    assert_geometry_unchanged,
    enforce_no_geometry_change_policy,
    estimate_translation_pixels,
)
from src.pipeline.io import load_image, sha256_file
from src.pipeline.manifest import append_manifest_entry
from src.pipeline.report import metrics, write_report
from src.pipeline.tone import apply_tone
from src.pipeline.validate import load_preset, load_schema, validate_preset


def _versions() -> dict[str, str]:
    def ver(pkg: str) -> str:
        return importlib.metadata.version(pkg)

    return {
        "python": platform.python_version(),
        "pillow": ver("Pillow"),
        "numpy": ver("numpy"),
        "jsonschema": ver("jsonschema"),
    }


def _collect_inputs(args: argparse.Namespace) -> list[Path]:
    if args.input:
        return [Path(args.input)]

    if args.input_dir:
        pattern = str(Path(args.input_dir) / args.glob)
        return [Path(p) for p in sorted(glob.glob(pattern))]

    raise ValueError("Either --input or --input-dir must be provided")


def _pixel_diff_metrics(ref_u8: np.ndarray, cand_u8: np.ndarray) -> tuple[float, float]:
    if ref_u8.shape != cand_u8.shape:
        raise ValueError("Pixel diff gate requires identical image dimensions")

    ref_gray = (
        ref_u8[..., 0].astype(np.float32) * 0.2126
        + ref_u8[..., 1].astype(np.float32) * 0.7152
        + ref_u8[..., 2].astype(np.float32) * 0.0722
    )
    cand_gray = (
        cand_u8[..., 0].astype(np.float32) * 0.2126
        + cand_u8[..., 1].astype(np.float32) * 0.7152
        + cand_u8[..., 2].astype(np.float32) * 0.0722
    )
    diff = np.abs(ref_gray - cand_gray)
    mae = float(diff.mean())
    diff_pixels_pct = float((diff > 0.0).mean() * 100.0)
    return mae, diff_pixels_pct


def _assert_clip_gate(arr_u8: np.ndarray, safety_cfg: dict) -> dict[str, float]:
    max_clip_pct = float(safety_cfg.get("max_channel_clip_pct", 1.0))
    clip_eval_mode = str(safety_cfg.get("clip_eval_mode", "any_channel"))
    clip_black_level = int(safety_cfg.get("clip_black_level", 0))
    clip_white_level = int(safety_cfg.get("clip_white_level", 255))

    m = metrics(
        arr_u8,
        clip_eval_mode=clip_eval_mode,
        clip_black_level=clip_black_level,
        clip_white_level=clip_white_level,
    )
    clip_pct = m["clipped_pct"]
    if clip_pct > max_clip_pct:
        raise ValueError(
            f"Clipping gate failed ({clip_eval_mode}): {clip_pct:.6f}% exceeds preset max {max_clip_pct:.6f}%"
        )
    return m


def _run_composition_gates(before: np.ndarray, work: np.ndarray, safety_cfg: dict) -> list[str]:
    qa_notes: list[str] = []

    if safety_cfg.get("no_geometry_change", True):
        assert_geometry_unchanged(before, work)
        qa_notes.append("PASS: geometry unchanged")

    if safety_cfg.get("no_geometry_change", True) and safety_cfg.get("identical_composition_expected", True):
        shift_x, shift_y = estimate_translation_pixels(before, work)
        max_shift = float(safety_cfg.get("max_translation_pixels", 0.0))
        if abs(shift_x) > max_shift or abs(shift_y) > max_shift:
            raise ValueError(
                f"Translation gate failed: estimated shift ({shift_x:.4f}, {shift_y:.4f}) exceeds max {max_shift:.4f}"
            )
        qa_notes.append(f"PASS: translation gate shift=({shift_x:.4f}, {shift_y:.4f})")

    if safety_cfg.get("pixel_diff_gate", False):
        mae, diff_pixels_pct = _pixel_diff_metrics(before, work)
        max_mae = float(safety_cfg.get("max_mae", 0.0))
        max_diff_pixels_pct = float(safety_cfg.get("max_diff_pixels_pct", 0.0))
        if mae > max_mae or diff_pixels_pct > max_diff_pixels_pct:
            raise ValueError(
                f"Pixel diff gate failed: mae={mae:.6f} (max {max_mae:.6f}), diff_pixels_pct={diff_pixels_pct:.6f}% (max {max_diff_pixels_pct:.6f}%)"
            )
        qa_notes.append(
            f"PASS: pixel diff gate mae={mae:.6f}, diff_pixels_pct={diff_pixels_pct:.6f}%"
        )

    return qa_notes


def process_image(
    input_path: Path,
    preset: dict,
    preset_path: Path,
    outdir: Path,
    reports_dir: Path,
    manifest_path: Path,
) -> dict:
    io_cfg = preset["io"]
    src_u8, meta = load_image(input_path, apply_exif_transpose=bool(io_cfg.get("exif_transpose", False)))
    input_hash = sha256_file(input_path)

    tone_cfg = preset["tone"]
    color_cfg = preset["color"]
    detail_cfg = preset["detail"]
    geometry_cfg = preset["geometry"]
    safety_cfg = preset["safety"]
    export_cfg = preset["export"]

    enforce_no_geometry_change_policy(safety_cfg, geometry_cfg)

    before = src_u8.copy()
    work = apply_tone(src_u8, tone_cfg)
    work = apply_color(work, color_cfg)
    work = apply_detail(work, detail_cfg)
    work, geometry_ops = apply_geometry(work, geometry_cfg)

    qa_notes = _run_composition_gates(before, work, safety_cfg)

    max_clip = float(safety_cfg.get("max_channel_clip_pct", 1.0))
    clip_metrics = _assert_clip_gate(work, safety_cfg)
    clip_pct = clip_metrics["clipped_pct"]
    qa_notes.append(
        f"PASS: clip gate ({safety_cfg.get('clip_eval_mode', 'any_channel')}) {clip_pct:.6f}% <= {max_clip:.6f}%"
    )

    export_paths = build_versioned_paths(outdir, input_path.stem, preset["name"], export_cfg)
    export_images(work, export_paths, export_cfg, meta.get("icc_profile"))

    outputs = {k: str(v.as_posix()) for k, v in export_paths.items()}
    output_hashes = {k: sha256_file(v) for k, v in export_paths.items()}

    clip_eval_mode = str(safety_cfg.get("clip_eval_mode", "any_channel"))
    clip_black_level = int(safety_cfg.get("clip_black_level", 0))
    clip_white_level = int(safety_cfg.get("clip_white_level", 255))
    before_metrics = metrics(
        before,
        clip_eval_mode=clip_eval_mode,
        clip_black_level=clip_black_level,
        clip_white_level=clip_white_level,
    )
    after_metrics = metrics(
        work,
        clip_eval_mode=clip_eval_mode,
        clip_black_level=clip_black_level,
        clip_white_level=clip_white_level,
    )

    report_name = f"{input_path.stem}_{preset['name'].replace(' ', '_').lower()}_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.md"
    report_path = reports_dir / report_name

    payload = {
        "output_name": next(iter(export_paths.values())).name,
        "input_path": str(input_path.as_posix()),
        "input_hash": input_hash,
        "preset_name": preset["name"],
        "preset_hash": sha256_file(preset_path),
        "versions": _versions(),
        "before": {
            "width": int(before.shape[1]),
            "height": int(before.shape[0]),
            **before_metrics,
        },
        "after": {
            "width": int(work.shape[1]),
            "height": int(work.shape[0]),
            **after_metrics,
        },
        "qa_notes": qa_notes if not geometry_ops else qa_notes + [f"Geometry ops: {', '.join(geometry_ops)}"],
        "outputs": outputs,
    }
    write_report(report_path, payload)

    manifest_entry = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "input_file": str(input_path.as_posix()),
        "input_hash": input_hash,
        "preset_file": str(preset_path.as_posix()),
        "preset_hash": sha256_file(preset_path),
        "output_files": outputs,
        "output_hashes": output_hashes,
        "report_file": str(report_path.as_posix()),
        "versions": _versions(),
        "settings": {
            "tone": tone_cfg,
            "color": color_cfg,
            "detail": detail_cfg,
            "geometry": geometry_cfg,
            "safety": safety_cfg,
            "export": export_cfg,
        },
    }
    append_manifest_entry(manifest_path, manifest_entry)
    return manifest_entry


def run_pipeline(preset_path: str | Path, input_paths: list[Path], outdir: str | Path, reports_dir: str | Path) -> list[dict]:
    preset_path = Path(preset_path)
    schema_path = Path("schemas/preset.schema.json")

    preset = load_preset(preset_path)
    schema = load_schema(schema_path)
    validate_preset(preset, schema)

    out_path = Path(outdir)
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    manifest_path = reports_path / "manifest.json"
    entries: list[dict] = []
    for input_path in input_paths:
        entries.append(
            process_image(
                Path(input_path),
                preset,
                preset_path,
                out_path,
                reports_path,
                manifest_path,
            )
        )
    return entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic enhance-only image pipeline")
    parser.add_argument("--preset", required=True, help="Path to preset JSON")
    parser.add_argument("--input", help="Path to one input image")
    parser.add_argument("--input-dir", help="Input directory for batch mode")
    parser.add_argument("--glob", default="*.png", help="Glob for batch mode")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--reports-dir", default="reports", help="Reports directory")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        input_paths = _collect_inputs(args)
        if not input_paths:
            raise ValueError("No input images matched the given arguments")
        run_pipeline(args.preset, input_paths, args.outdir, args.reports_dir)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
