from __future__ import annotations

import numpy as np

from .types import Config, ImageU8


def _clip01(arr: np.ndarray) -> np.ndarray:
    return np.clip(arr, 0.0, 1.0)


def _apply_white_balance(arr: np.ndarray, wb_mode: str) -> np.ndarray:
    mode = wb_mode.lower()
    if mode == "none":
        return arr

    if mode == "daylight":
        gains = np.array([1.03, 1.0, 0.97], dtype=np.float32)
        return _clip01(arr * gains)

    if mode == "tungsten":
        gains = np.array([0.92, 1.0, 1.12], dtype=np.float32)
        return _clip01(arr * gains)

    if mode == "auto":
        means = arr.reshape(-1, 3).mean(axis=0)
        mean_gray = float(np.mean(means))
        denom = np.maximum(means, 1e-6)
        gains = mean_gray / denom
        gains = np.clip(gains, 0.85, 1.15).astype(np.float32)
        return _clip01(arr * gains)

    raise ValueError(f"Unsupported wb_mode: {wb_mode}")


def apply_color(arr_u8: ImageU8, cfg: Config) -> ImageU8:
    arr = arr_u8.astype(np.float32) / 255.0

    saturation = float(cfg.get("saturation", 0.0))
    vibrance = float(cfg.get("vibrance", 0.0))
    wb_mode = str(cfg.get("wb_mode", "none"))

    arr = _apply_white_balance(arr, wb_mode)

    if saturation != 0.0:
        gray = arr.mean(axis=2, keepdims=True)
        arr = gray + (arr - gray) * (1.0 + saturation)

    if vibrance != 0.0:
        gray = arr.mean(axis=2, keepdims=True)
        sat_measure = np.max(arr, axis=2, keepdims=True) - np.min(arr, axis=2, keepdims=True)
        vibrance_strength = np.clip(1.0 - sat_measure, 0.0, 1.0) * vibrance
        arr = arr + (arr - gray) * vibrance_strength

    arr = _clip01(arr)
    return (arr * 255.0 + 0.5).astype(np.uint8)
