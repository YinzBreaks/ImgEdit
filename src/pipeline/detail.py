from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def apply_detail(arr_u8: np.ndarray, cfg: dict) -> np.ndarray:
    denoise_strength = float(cfg.get("denoise_strength", 0.0))
    sharpen_amount = float(cfg.get("sharpen_amount", 0.0))
    sharpen_radius = float(cfg.get("sharpen_radius", 1.0))

    image = Image.fromarray(arr_u8, mode="RGB")

    if denoise_strength > 0.0:
        denoised = image.filter(ImageFilter.GaussianBlur(radius=max(0.0, denoise_strength * 1.5)))
        alpha = min(1.0, denoise_strength)
        image = Image.blend(image, denoised, alpha=alpha)

    if sharpen_amount > 0.0:
        percent = int(max(0.0, sharpen_amount) * 100)
        image = image.filter(
            ImageFilter.UnsharpMask(
                radius=max(0.1, sharpen_radius),
                percent=percent,
                threshold=2,
            )
        )

    return np.asarray(image, dtype=np.uint8)
