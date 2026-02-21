from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import platform
import sys
from pathlib import Path
from typing import Any, cast

import numpy as np
from PIL import UnidentifiedImageError

from .pipeline.color import apply_color
from .pipeline.detail import apply_detail
from .pipeline.export import build_versioned_paths, export_images
from .pipeline.geometry import (
    apply_geometry,
    assert_geometry_unchanged,
    enforce_no_geometry_change_policy,
    estimate_translation_pixels,
)
from .pipeline.io import load_image, sha256_file
from .pipeline.manifest import append_manifest_entry
from .pipeline.naming import slugify
from .pipeline.report import metrics, write_report
from .pipeline.tone import apply_tone
from .pipeline.types import ManifestEntry, ReportPayload
from .pipeline.validate import load_preset, load_schema, validate_preset
from .types import Preset, SafetyConfig


class PipelineGateError(ValueError):
    def __init__(self, gate: str, message: str) -> None:
        super().__init__(message)
        self.gate = gate


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
    input_provided = args.input is not None
    input_dir_provided = args.input_dir is not None
    if not (input_provided ^ input_dir_provided):
        raise ValueError("Provide exactly one of --input or --input-dir")

    max_files = int(args.max_files) if args.max_files is not None else None
    if max_files is not None and max_files <= 0:
        raise ValueError("--max-files must be a positive integer")

    if args.input:
        return [Path(args.input)]

    return _discover_inputs(
        input_dir=Path(args.input_dir),
        glob_pattern=args.glob,
        recursive=bool(args.recursive),
        include_ext_csv=args.include_ext,
        max_files=max_files,
    )


def _parse_include_ext(include_ext_csv: str) -> set[str]:
    return {
        token.strip().lower().lstrip(".")
        for token in include_ext_csv.split(",")
        if token.strip()
    }


def _norm_relpath(path: Path, input_dir: Path) -> str:
    return path.relative_to(input_dir).as_posix()


def _discover_inputs(
    input_dir: Path,
    glob_pattern: str,
    recursive: bool,
    include_ext_csv: str,
    max_files: int | None,
) -> list[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")

    include_ext = _parse_include_ext(include_ext_csv)

    if recursive:
        candidates = [p for p in input_dir.rglob("*") if p.is_file()]
        if include_ext:
            candidates = [p for p in candidates if p.suffix.lower().lstrip(".") in include_ext]
    else:
        candidates = [p for p in input_dir.glob(glob_pattern) if p.is_file()]

    # Sort by normalized relative POSIX path in a case-insensitive way. Using
    # .casefold() (rather than .lower()) provides robust, locale-independent
    # case-insensitive ordering while still matching the documented "normalized
    # relative POSIX path" sorting behavior.
    sorted_candidates = sorted(
        candidates,
        key=lambda p: _norm_relpath(p, input_dir).casefold(),
    )

    if max_files is not None:
        return sorted_candidates[:max_files]
    return sorted_candidates


def _slugify(value: str) -> str:
    """
    Internal helper to centralize the default slugify fallback used by the CLI.

    By keeping this wrapper, we ensure that any change to the slugification
    fallback behavior only needs to be made in one place, and that all CLI
    consumers use a consistent policy.
    """
    return slugify(value, fallback="value")


def _failed_gate_label(error: Exception) -> str:
    if isinstance(error, PipelineGateError):
        return error.gate

    msg = str(error).lower()
    if "translation gate failed" in msg:
        return "translation"
    if "pixel diff gate failed" in msg:
        return "pixel_diff"
    if "clipping gate failed" in msg:
        return "clipping"
    if "geometry changed unexpectedly" in msg or "no_geometry_change" in msg:
        return "geometry"
    if "cannot identify image file" in msg or "truncated" in msg:
        return "input_decode"
    return "pipeline"


def _write_failure_report(
    reports_dir: Path,
    input_path: Path,
    preset_name: str,
    error: Exception,
) -> Path:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{_slugify(input_path.stem)}_{_slugify(preset_name)}_{timestamp}_FAIL.md"
    report_path = reports_dir / filename
    gate = _failed_gate_label(error)

    body = (
        "# Failure Report\n\n"
        f"- Input: `{input_path.as_posix()}`\n"
        f"- Preset: `{preset_name}`\n"
        f"- Timestamp (UTC): `{timestamp}`\n"
        f"- Failed Gate: `{gate}`\n"
        f"- Error: `{error}`\n"
    )
    report_path.write_text(body, encoding="utf-8")
    return report_path


def _write_batch_summary(
    reports_dir: Path,
    *,
    preset_name: str,
    preset_hash: str,
    mode: str,
    input_dir: Path | None,
    recursive: bool,
    include_ext: str,
    glob_pattern: str,
    max_files: int | None,
    discovered: list[Path],
    processed_ok: int,
    failures: list[dict[str, str]],
    manifest_path: Path | None,
    outdir: Path,
    include_relpath_slug: bool,
    planned_outputs: list[dict[str, str]] | None = None,
) -> Path:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = reports_dir / f"batch_{timestamp}.md"

    lines = [
        "# Batch Summary",
        "",
        f"- preset: `{preset_name}`",
        f"- preset_hash: `{preset_hash}`",
        f"- mode: `{mode}`",
        f"- input_dir: `{input_dir.as_posix() if input_dir else 'none'}`",
        f"- recursive: `{str(recursive).lower()}`",
        f"- include_ext: `{include_ext}`",
        f"- glob: `{glob_pattern}`",
        f"- max_files: `{max_files if max_files is not None else 'none'}`",
        f"- total_discovered: `{len(discovered)}`",
        f"- processed_ok: `{processed_ok}`",
        f"- failed: `{len(failures)}`",
        f"- manifest: `{manifest_path.as_posix() if manifest_path else 'none'}`",
        f"- outdir: `{outdir.as_posix()}`",
        f"- naming_mode: `include_relpath_slug={str(include_relpath_slug).lower()}`",
        "",
    ]

    if failures:
        lines.append("## Failures")
        lines.append("")
        for failure in failures:
            lines.append(f"- `{failure['path']}` -> `{failure['error']}`")
        lines.append("")

    if mode == "dry-run" and planned_outputs:
        lines.append("## Planned Outputs")
        lines.append("")
        for row in planned_outputs:
            lines.append(f"- input: `{row['input']}`")
            if row.get("master"):
                lines.append(f"  - master: `{row['master']}`")
            if row.get("web"):
                lines.append(f"  - web: `{row['web']}`")
        lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


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


def _assert_clip_gate(arr_u8: np.ndarray, safety_cfg: SafetyConfig) -> dict[str, float]:
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
        raise PipelineGateError(
            "clipping",
            f"Clipping gate failed ({clip_eval_mode}): {clip_pct:.6f}% exceeds preset max {max_clip_pct:.6f}%"
        )
    return m


def _run_composition_gates(before: np.ndarray, work: np.ndarray, safety_cfg: SafetyConfig) -> list[str]:
    qa_notes: list[str] = []

    if safety_cfg.get("no_geometry_change", True):
        try:
            assert_geometry_unchanged(before, work)
        except Exception as exc:
            raise PipelineGateError("geometry", str(exc)) from exc
        qa_notes.append("PASS: geometry unchanged")

    if safety_cfg.get("no_geometry_change", True) and safety_cfg.get("identical_composition_expected", True):
        shift_x, shift_y = estimate_translation_pixels(before, work)
        max_shift = float(safety_cfg.get("max_translation_pixels", 0.0))
        if abs(shift_x) > max_shift or abs(shift_y) > max_shift:
            raise PipelineGateError(
                "translation",
                f"Translation gate failed: estimated shift ({shift_x:.4f}, {shift_y:.4f}) exceeds max {max_shift:.4f}"
            )
        qa_notes.append(f"PASS: translation gate shift=({shift_x:.4f}, {shift_y:.4f})")

    if safety_cfg.get("pixel_diff_gate", False):
        mae, diff_pixels_pct = _pixel_diff_metrics(before, work)
        max_mae = float(safety_cfg.get("max_mae", 0.0))
        max_diff_pixels_pct = float(safety_cfg.get("max_diff_pixels_pct", 0.0))
        if mae > max_mae or diff_pixels_pct > max_diff_pixels_pct:
            raise PipelineGateError(
                "pixel_diff",
                f"Pixel diff gate failed: mae={mae:.6f} (max {max_mae:.6f}), diff_pixels_pct={diff_pixels_pct:.6f}% (max {max_diff_pixels_pct:.6f}%)"
            )
        qa_notes.append(
            f"PASS: pixel diff gate mae={mae:.6f}, diff_pixels_pct={diff_pixels_pct:.6f}%"
        )

    return qa_notes


def process_image(
    input_path: Path,
    relative_input_path: Path | None,
    preset: Preset,
    preset_path: Path,
    outdir: Path,
    reports_dir: Path,
    manifest_path: Path,
) -> ManifestEntry:
    io_cfg = preset["io"]
    try:
        src_u8, meta = load_image(input_path, apply_exif_transpose=bool(io_cfg.get("exif_transpose", False)))
    except (UnidentifiedImageError, OSError) as exc:
        raise PipelineGateError("input_decode", str(exc)) from exc
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

    export_paths = build_versioned_paths(
        outdir,
        input_path.stem,
        preset["name"],
        export_cfg,
        relative_input_path=relative_input_path,
    )
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

    payload: ReportPayload = {
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

    manifest_entry: ManifestEntry = {
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


def run_pipeline(
    preset_path: str | Path,
    input_paths: list[Path],
    outdir: str | Path,
    reports_dir: str | Path,
) -> list[dict[str, Any]]:
    result = run_pipeline_batch(
        preset_path=preset_path,
        input_paths=input_paths,
        input_dir=None,
        recursive=False,
        include_ext="png,jpg,jpeg",
        glob_pattern="*.png",
        outdir=outdir,
        reports_dir=reports_dir,
        on_error="stop",
        dry_run=False,
        max_files=None,
    )
    return result["entries"]


def run_pipeline_batch(
    preset_path: str | Path,
    input_paths: list[Path],
    input_dir: Path | None,
    recursive: bool,
    include_ext: str,
    glob_pattern: str,
    outdir: str | Path,
    reports_dir: str | Path,
    on_error: str,
    dry_run: bool,
    max_files: int | None,
) -> dict[str, Any]:
    preset_path = Path(preset_path)
    schema_path = Path("schemas/preset.schema.json")

    preset_raw: Any = load_preset(preset_path)
    schema_raw: Any = load_schema(schema_path)
    validate_preset(preset_raw, schema_raw)
    preset = cast(Preset, preset_raw)

    out_path = Path(outdir)
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    manifest_path = reports_path / "manifest.json"
    entries: list[ManifestEntry] = []
    failures: list[dict[str, str]] = []
    planned_outputs: list[dict[str, str]] = []

    if dry_run:
        for input_path in input_paths:
            rel = input_path.relative_to(input_dir) if input_dir else Path(input_path.name)
            export_paths = build_versioned_paths(
                out_path,
                input_path.stem,
                preset["name"],
                preset["export"],
                relative_input_path=rel,
            )
            row = {"input": input_path.as_posix()}
            if "master" in export_paths:
                row["master"] = export_paths["master"].as_posix()
            if "web" in export_paths:
                row["web"] = export_paths["web"].as_posix()
            planned_outputs.append(row)

        summary_path = _write_batch_summary(
            reports_path,
            preset_name=preset["name"],
            preset_hash=sha256_file(preset_path),
            mode="dry-run",
            input_dir=input_dir,
            recursive=recursive,
            include_ext=include_ext,
            glob_pattern=glob_pattern,
            max_files=max_files,
            discovered=input_paths,
            processed_ok=0,
            failures=failures,
            manifest_path=None,
            outdir=out_path,
            include_relpath_slug=bool(preset["export"].get("include_relpath_slug", False)),
            planned_outputs=planned_outputs,
        )
        return {
            "entries": entries,
            "failures": failures,
            "summary_path": summary_path,
            "manifest_path": None,
            "planned_outputs": planned_outputs,
        }

    for input_path in input_paths:
        rel = input_path.relative_to(input_dir) if input_dir else Path(input_path.name)
        try:
            entries.append(
                process_image(
                    Path(input_path),
                    rel,
                    preset,
                    preset_path,
                    out_path,
                    reports_path,
                    manifest_path,
                )
            )
        except Exception as exc:
            if on_error == "stop":
                raise
            failure_report = _write_failure_report(reports_path, Path(input_path), preset["name"], exc)
            failures.append(
                {
                    "path": Path(input_path).as_posix(),
                    "error": str(exc),
                    "failure_report": failure_report.as_posix(),
                }
            )

    summary_path = _write_batch_summary(
        reports_path,
        preset_name=preset["name"],
        preset_hash=sha256_file(preset_path),
        mode="run",
        input_dir=input_dir,
        recursive=recursive,
        include_ext=include_ext,
        glob_pattern=glob_pattern,
        max_files=max_files,
        discovered=input_paths,
        processed_ok=len(entries),
        failures=failures,
        manifest_path=manifest_path,
        outdir=out_path,
        include_relpath_slug=bool(preset["export"].get("include_relpath_slug", False)),
        planned_outputs=None,
    )

    return {
        "entries": entries,
        "failures": failures,
        "summary_path": summary_path,
        "manifest_path": manifest_path,
        "planned_outputs": planned_outputs,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic enhance-only image pipeline")
    parser.add_argument("--preset", required=True, help="Path to preset JSON")
    parser.add_argument("--input", help="Path to one input image")
    parser.add_argument("--input-dir", help="Input directory for batch mode")
    parser.add_argument("--glob", default="*.png", help="Glob for batch mode")
    parser.add_argument("--recursive", action="store_true", help="Recursively discover files when using --input-dir")
    parser.add_argument(
        "--include-ext",
        default="png,jpg,jpeg",
        help="Comma-separated extensions for recursive discovery, e.g. png,jpg,jpeg",
    )
    parser.add_argument("--on-error", choices=["stop", "continue"], default="stop", help="Error policy")
    parser.add_argument("--dry-run", action="store_true", help="Audit planned outputs without reading/writing image pixels")
    parser.add_argument("--max-files", type=int, default=None, help="Limit processed/listed files")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--reports-dir", default="reports", help="Reports directory")
    return parser


def main() -> int:
    parser = build_parser()
    argv = sys.argv[1:]
    if argv and argv[0] == "batch":
        argv = argv[1:]
    args = parser.parse_args(argv)

    try:
        input_paths = _collect_inputs(args)
        if not input_paths:
            raise ValueError("No input images matched the given arguments")
        result = run_pipeline_batch(
            preset_path=args.preset,
            input_paths=input_paths,
            input_dir=Path(args.input_dir) if args.input_dir else None,
            recursive=bool(args.recursive),
            include_ext=args.include_ext,
            glob_pattern=args.glob,
            outdir=args.outdir,
            reports_dir=args.reports_dir,
            on_error=args.on_error,
            dry_run=bool(args.dry_run),
            max_files=args.max_files,
        )
        if result["failures"]:
            return 1
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
