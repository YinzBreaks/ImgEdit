from __future__ import annotations

import re
from pathlib import Path

from .io import save_image


def _slugify(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return clean or "preset"


def build_versioned_paths(
    outdir: str | Path,
    input_stem: str,
    preset_name: str,
    export_cfg: dict,
) -> dict[str, Path]:
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    stem = f"{_slugify(input_stem)}_{_slugify(preset_name)}"
    keep_png_master = bool(export_cfg.get("keep_png_master", True))
    web_enabled = bool(export_cfg.get("web_enabled", False))
    web_format = str(export_cfg.get("web_format", "jpeg")).lower()

    version = 1
    while True:
        suffix = f"_v{version:03d}"
        master_path = out_path / f"{stem}{suffix}.png"
        web_path = out_path / f"{stem}{suffix}.{'jpg' if web_format in {'jpg', 'jpeg'} else web_format}"

        candidates = [master_path] if keep_png_master else []
        if web_enabled:
            candidates.append(web_path)

        if not any(path.exists() for path in candidates):
            break
        version += 1

    result: dict[str, Path] = {}
    if keep_png_master:
        result["master"] = master_path
    if web_enabled:
        result["web"] = web_path
    return result


def export_images(arr, export_paths: dict[str, Path], export_cfg: dict, icc_profile: bytes | None) -> None:
    embed_profile = bool(export_cfg.get("embed_profile", True))

    if "master" in export_paths:
        save_image(arr, export_paths["master"], "PNG", embed_profile=embed_profile, icc_profile=icc_profile)

    if "web" in export_paths:
        quality = int(export_cfg.get("web_quality", 90))
        fmt = str(export_cfg.get("web_format", "jpeg")).upper()
        save_image(
            arr,
            export_paths["web"],
            fmt,
            quality=quality,
            embed_profile=embed_profile,
            icc_profile=icc_profile,
        )
