from __future__ import annotations

from pathlib import Path

from .types import ImageU8, ReportPayload


def metrics(
    arr_u8: ImageU8,
    *,
    clip_eval_mode: str = "any_channel",
    clip_black_level: int = 0,
    clip_white_level: int = 255,
) -> dict[str, float]: ...

def write_report(report_path: str | Path, payload: ReportPayload) -> None: ...
