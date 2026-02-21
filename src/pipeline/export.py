from __future__ import annotations

from pathlib import Path

from .io import save_image
from .naming import slugify
from .types import Config, ImageU8


def _relpath_slug(relative_input_path: str | Path) -> str:
    rel = Path(relative_input_path)
    no_suffix = rel.with_suffix("")
    parts = [part for part in no_suffix.parts if part not in {".", ""}]
    slug_parts = [slugify(part, fallback="part") for part in parts]
    rel_slug = "__".join(part for part in slug_parts if part)
    if not parts or not rel_slug:
        raise ValueError(
            "include_relpath_slug requires a relative input path that contains at least one usable "
            "directory or file component after filtering out '.' and empty segments, and that "
            "normalizes to a non-empty slug (for example, 'folder/file', not '.', './', an empty "
            f"string, or components that all slugify to empty): {relative_input_path}"
        )
    return rel_slug


def build_output_stem(
    input_stem: str,
    preset_name: str,
    export_cfg: Config,
    relative_input_path: str | Path | None = None,
) -> str:
    preset_slug = slugify(preset_name, fallback="preset")
    include_relpath_slug = bool(export_cfg.get("include_relpath_slug", False))

    if include_relpath_slug:
        if relative_input_path is None:
            raise ValueError("include_relpath_slug=true requires relative_input_path")
        rel_slug = _relpath_slug(relative_input_path)
        return f"{rel_slug}_{preset_slug}"

    return f"{slugify(input_stem, fallback='preset')}_{preset_slug}"


def build_versioned_paths(
    outdir: str | Path,
    input_stem: str,
    preset_name: str,
    export_cfg: Config,
    relative_input_path: str | Path | None = None,
) -> dict[str, Path]:
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    stem = build_output_stem(
        input_stem=input_stem,
        preset_name=preset_name,
        export_cfg=export_cfg,
        relative_input_path=relative_input_path,
    )
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


def export_images(
    arr: ImageU8,
    export_paths: dict[str, Path],
    export_cfg: Config,
    icc_profile: bytes | None,
) -> None:
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
