from __future__ import annotations

import numpy as np


def _clip01(arr: np.ndarray) -> np.ndarray:
    return np.clip(arr, 0.0, 1.0)


def apply_tone(arr_u8: np.ndarray, cfg: dict) -> np.ndarray:
    arr = arr_u8.astype(np.float32) / 255.0

    exposure_ev = float(cfg.get("exposure_ev", 0.0))
    contrast = float(cfg.get("contrast", 0.0))
    black_point = float(cfg.get("black_point", 0.0))
    white_point = float(cfg.get("white_point", 0.0))

    if exposure_ev != 0.0:
        arr = arr * (2.0**exposure_ev)

    if contrast != 0.0:
        arr = (arr - 0.5) * (1.0 + contrast) + 0.5

    white = max(1e-6, 1.0 - white_point)
    black = min(0.999, max(0.0, black_point))
    if white <= black:
        white = min(1.0, black + 1e-3)

    arr = (arr - black) / (white - black)
    arr = _clip01(arr)
    return (arr * 255.0 + 0.5).astype(np.uint8)
