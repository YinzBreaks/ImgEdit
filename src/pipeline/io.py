from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_image(path: str | Path, *, apply_exif_transpose: bool = False) -> tuple[np.ndarray, dict[str, Any]]:
    image_path = Path(path)
    with Image.open(image_path) as img:
        if apply_exif_transpose:
            img = ImageOps.exif_transpose(img)
        icc_profile = img.info.get("icc_profile")
        rgb = img.convert("RGB")
        arr = np.asarray(rgb, dtype=np.uint8)
    meta: dict[str, Any] = {"icc_profile": icc_profile}
    return arr, meta


def _to_pil(arr: np.ndarray) -> Image.Image:
    clipped = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(clipped, mode="RGB")


def save_image(
    arr: np.ndarray,
    path: str | Path,
    fmt: str,
    *,
    quality: int = 92,
    embed_profile: bool = True,
    icc_profile: bytes | None = None,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image = _to_pil(arr)

    fmt_upper = fmt.upper()
    save_kwargs: dict[str, Any] = {}
    if embed_profile and icc_profile:
        save_kwargs["icc_profile"] = icc_profile

    if fmt_upper == "PNG":
        image.save(target, format="PNG", compress_level=9, optimize=False, **save_kwargs)
        return

    if fmt_upper in {"JPG", "JPEG"}:
        image.save(
            target,
            format="JPEG",
            quality=int(quality),
            optimize=False,
            progressive=False,
            subsampling=0,
            **save_kwargs,
        )
        return

    raise ValueError(f"Unsupported format for deterministic export: {fmt}")
