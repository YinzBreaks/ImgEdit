from __future__ import annotations

from typing import Any, Mapping, TypedDict

import numpy as np
import numpy.typing as npt

ImageU8 = npt.NDArray[np.uint8]
Config = Mapping[str, Any]


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
