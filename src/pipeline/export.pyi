from __future__ import annotations

from pathlib import Path

from .types import Config, ImageU8


def build_versioned_paths(
    outdir: str | Path,
    input_stem: str,
    preset_name: str,
    export_cfg: Config,
    relative_input_path: str | Path | None = None,
) -> dict[str, Path]: ...

def export_images(
    arr: ImageU8,
    export_paths: dict[str, Path],
    export_cfg: Config,
    icc_profile: bytes | None,
) -> None: ...
