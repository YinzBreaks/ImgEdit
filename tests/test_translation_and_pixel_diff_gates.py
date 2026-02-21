import numpy as np
import pytest

from src.cli import _run_composition_gates


def _base_image() -> np.ndarray:
    arr = np.zeros((32, 32, 3), dtype=np.uint8)
    arr[..., 0] = np.tile(np.arange(32, dtype=np.uint8), (32, 1))
    arr[..., 1] = 90
    arr[..., 2] = 140
    return arr


def test_translation_gate_catches_1px_shift() -> None:
    before = _base_image()
    shifted = np.roll(before, shift=1, axis=1)

    safety = {
        "no_geometry_change": True,
        "identical_composition_expected": True,
        "max_translation_pixels": 0.0,
        "pixel_diff_gate": False,
        "max_mae": 0.0,
        "max_diff_pixels_pct": 0.0,
    }

    with pytest.raises(ValueError, match="Translation gate failed"):
        _run_composition_gates(before, shifted, safety)


def test_pixel_diff_gate_catches_small_edit() -> None:
    before = _base_image()
    edited = before.copy()
    edited[0, 0, 0] = min(255, int(edited[0, 0, 0]) + 1)

    safety = {
        "no_geometry_change": True,
        "identical_composition_expected": False,
        "max_translation_pixels": 0.0,
        "pixel_diff_gate": True,
        "max_mae": 0.0,
        "max_diff_pixels_pct": 0.0,
    }

    with pytest.raises(ValueError, match="Pixel diff gate failed"):
        _run_composition_gates(before, edited, safety)
