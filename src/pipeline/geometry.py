from __future__ import annotations

import numpy as np
from PIL import Image


def _is_geometry_requested(geometry_cfg: dict) -> bool:
    if not geometry_cfg.get("enabled", False):
        return False
    crop = geometry_cfg.get("crop", {})
    resize = geometry_cfg.get("resize", {})
    return bool(crop.get("enabled", False) or resize.get("enabled", False))


def enforce_no_geometry_change_policy(safety_cfg: dict, geometry_cfg: dict) -> None:
    if safety_cfg.get("no_geometry_change", True) and _is_geometry_requested(geometry_cfg):
        raise ValueError("Preset violates no_geometry_change: geometry operations are enabled")


def apply_geometry(arr_u8: np.ndarray, geometry_cfg: dict) -> tuple[np.ndarray, list[str]]:
    ops: list[str] = []
    if not geometry_cfg.get("enabled", False):
        return arr_u8, ops

    current = arr_u8
    crop_cfg = geometry_cfg.get("crop", {})
    if crop_cfg.get("enabled", False):
        x = int(crop_cfg["x"])
        y = int(crop_cfg["y"])
        width = int(crop_cfg["width"])
        height = int(crop_cfg["height"])
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError("Invalid crop rectangle")
        if x + width > current.shape[1] or y + height > current.shape[0]:
            raise ValueError("Crop rectangle is outside image bounds")
        current = current[y : y + height, x : x + width]
        ops.append(f"crop({x},{y},{width},{height})")

    resize_cfg = geometry_cfg.get("resize", {})
    if resize_cfg.get("enabled", False):
        width = int(resize_cfg["width"])
        height = int(resize_cfg["height"])
        if width <= 0 or height <= 0:
            raise ValueError("Invalid resize dimensions")
        resample_name = str(resize_cfg.get("resample", "lanczos")).lower()
        resample_map = {
            "nearest": Image.Resampling.NEAREST,
            "bilinear": Image.Resampling.BILINEAR,
            "bicubic": Image.Resampling.BICUBIC,
            "lanczos": Image.Resampling.LANCZOS,
        }
        if resample_name not in resample_map:
            raise ValueError(f"Unsupported resample mode: {resample_name}")
        pil_img = Image.fromarray(current, mode="RGB")
        pil_img = pil_img.resize((width, height), resample=resample_map[resample_name])
        current = np.asarray(pil_img, dtype=np.uint8)
        ops.append(f"resize({width},{height},{resample_name})")

    return current, ops


def assert_geometry_unchanged(before: np.ndarray, after: np.ndarray) -> None:
    if before.shape != after.shape:
        raise ValueError(
            f"Geometry changed unexpectedly: {before.shape[1]}x{before.shape[0]} -> {after.shape[1]}x{after.shape[0]}"
        )


def estimate_translation_pixels(ref_u8: np.ndarray, cand_u8: np.ndarray) -> tuple[float, float]:
    if ref_u8.shape != cand_u8.shape:
        raise ValueError("Cannot estimate translation on arrays with different shapes")

    ref_gray = ref_u8.astype(np.float32).mean(axis=2)
    cand_gray = cand_u8.astype(np.float32).mean(axis=2)

    ref_gray -= ref_gray.mean()
    cand_gray -= cand_gray.mean()

    ref_fft = np.fft.fft2(ref_gray)
    cand_fft = np.fft.fft2(cand_gray)
    cross = ref_fft * np.conj(cand_fft)
    denom = np.abs(cross)
    denom[denom == 0] = 1.0
    phase = cross / denom
    corr = np.fft.ifft2(phase)
    corr_abs = np.abs(corr)

    max_index = np.unravel_index(np.argmax(corr_abs), corr_abs.shape)
    shift_y = float(max_index[0])
    shift_x = float(max_index[1])

    height, width = corr_abs.shape
    if shift_y > height / 2:
        shift_y -= height
    if shift_x > width / 2:
        shift_x -= width

    return shift_x, shift_y
