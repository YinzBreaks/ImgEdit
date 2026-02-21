import numpy as np
import pytest

from src.cli import _assert_clip_gate


def _sample_image() -> np.ndarray:
    arr = np.full((10, 10, 3), 100, dtype=np.uint8)
    arr[0, 0, 0] = 255
    return arr


def test_clipping_mode_any_channel() -> None:
    arr = _sample_image()
    safety = {
        "max_channel_clip_pct": 0.5,
        "clip_eval_mode": "any_channel",
        "clip_black_level": 0,
        "clip_white_level": 250,
    }
    with pytest.raises(ValueError):
        _assert_clip_gate(arr, safety)

    safety["max_channel_clip_pct"] = 1.0
    m = _assert_clip_gate(arr, safety)
    assert m["clipped_pct"] == pytest.approx(1.0)


def test_clipping_mode_luma_only() -> None:
    arr = _sample_image()
    safety = {
        "max_channel_clip_pct": 0.0,
        "clip_eval_mode": "luma_only",
        "clip_black_level": 0,
        "clip_white_level": 250,
    }
    m = _assert_clip_gate(arr, safety)
    assert m["clipped_pct"] == pytest.approx(0.0)


def test_clipping_mode_per_channel() -> None:
    arr = _sample_image()
    safety = {
        "max_channel_clip_pct": 0.5,
        "clip_eval_mode": "per_channel",
        "clip_black_level": 0,
        "clip_white_level": 250,
    }
    with pytest.raises(ValueError):
        _assert_clip_gate(arr, safety)

    safety["max_channel_clip_pct"] = 1.0
    m = _assert_clip_gate(arr, safety)
    assert m["clipped_pct"] == pytest.approx(1.0)
    assert m["clipped_pct_r"] == pytest.approx(1.0)
    assert m["clipped_pct_g"] == pytest.approx(0.0)
    assert m["clipped_pct_b"] == pytest.approx(0.0)
