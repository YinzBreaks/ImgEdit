from __future__ import annotations

from pathlib import Path

import numpy as np


def metrics(
    arr_u8: np.ndarray,
    *,
    clip_eval_mode: str = "any_channel",
    clip_black_level: int = 0,
    clip_white_level: int = 255,
) -> dict[str, float]:
    arr = arr_u8.astype(np.float32) / 255.0
    luma = arr[..., 0] * 0.2126 + arr[..., 1] * 0.7152 + arr[..., 2] * 0.0722
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    sat_proxy = float((mx - mn).mean())

    arr_i = arr_u8.astype(np.int16)
    clipped_by_channel = (arr_i <= int(clip_black_level)) | (arr_i >= int(clip_white_level))
    channel_pcts = clipped_by_channel.mean(axis=(0, 1)) * 100.0

    if clip_eval_mode == "any_channel":
        clip_pct = float(np.any(clipped_by_channel, axis=2).mean() * 100.0)
    elif clip_eval_mode == "luma_only":
        luma_u8 = (
            arr_u8[..., 0].astype(np.float32) * 0.2126
            + arr_u8[..., 1].astype(np.float32) * 0.7152
            + arr_u8[..., 2].astype(np.float32) * 0.0722
        )
        clip_pct = float(((luma_u8 <= clip_black_level) | (luma_u8 >= clip_white_level)).mean() * 100.0)
    elif clip_eval_mode == "per_channel":
        clip_pct = float(channel_pcts.max())
    else:
        raise ValueError(f"Unsupported clip_eval_mode: {clip_eval_mode}")

    return {
        "mean_luminance": float(luma.mean()),
        "saturation_proxy": sat_proxy,
        "clipped_pct": clip_pct,
        "clipped_pct_r": float(channel_pcts[0]),
        "clipped_pct_g": float(channel_pcts[1]),
        "clipped_pct_b": float(channel_pcts[2]),
    }


def write_report(report_path: str | Path, payload: dict) -> None:
    out = Path(report_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Image Report: {payload['output_name']}",
        "",
        "## Inputs",
        f"- Input path: {payload['input_path']}",
        f"- Input SHA256: {payload['input_hash']}",
        f"- Preset: {payload['preset_name']}",
        f"- Preset SHA256: {payload['preset_hash']}",
        "",
        "## Versions",
        f"- Python: {payload['versions']['python']}",
        f"- Pillow: {payload['versions']['pillow']}",
        f"- NumPy: {payload['versions']['numpy']}",
        f"- jsonschema: {payload['versions']['jsonschema']}",
        "",
        "## Before / After",
        f"- Dimensions before: {payload['before']['width']}x{payload['before']['height']}",
        f"- Dimensions after: {payload['after']['width']}x{payload['after']['height']}",
        f"- Mean luminance before: {payload['before']['mean_luminance']:.6f}",
        f"- Mean luminance after: {payload['after']['mean_luminance']:.6f}",
        f"- Saturation proxy before: {payload['before']['saturation_proxy']:.6f}",
        f"- Saturation proxy after: {payload['after']['saturation_proxy']:.6f}",
        f"- Clipped pixels % before: {payload['before']['clipped_pct']:.6f}",
        f"- Clipped pixels % after: {payload['after']['clipped_pct']:.6f}",
        "",
        "## QA Gates",
    ]

    for note in payload["qa_notes"]:
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Outputs",
    ])

    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
