from __future__ import annotations

from typing import Any, TypedDict


class SafetyConfig(TypedDict):
    max_channel_clip_pct: float
    clip_eval_mode: str
    clip_black_level: int
    clip_white_level: int
    no_geometry_change: bool
    identical_composition_expected: bool
    max_translation_pixels: float
    pixel_diff_gate: bool
    max_mae: float
    max_diff_pixels_pct: float


class Preset(TypedDict):
    name: str
    io: dict[str, Any]
    tone: dict[str, Any]
    color: dict[str, Any]
    detail: dict[str, Any]
    geometry: dict[str, Any]
    safety: SafetyConfig
    export: dict[str, Any]


class ManifestEntry(TypedDict):
    timestamp_utc: str
    input_file: str
    input_hash: str
    preset_file: str
    preset_hash: str
    output_files: dict[str, str]
    output_hashes: dict[str, str]
    report_file: str
    versions: dict[str, str]
    settings: dict[str, Any]


class ReportPayload(TypedDict):
    output_name: str
    input_path: str
    input_hash: str
    preset_name: str
    preset_hash: str
    versions: dict[str, str]
    before: dict[str, Any]
    after: dict[str, Any]
    qa_notes: list[str]
    outputs: dict[str, str]
