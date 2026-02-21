import pytest

from src.pipeline.geometry import enforce_no_geometry_change_policy


def test_no_geometry_change_policy_rejects_geometry_ops() -> None:
    safety = {
        "no_geometry_change": True,
        "identical_composition_expected": True,
        "max_translation_pixels": 0.0,
    }
    geometry = {
        "enabled": True,
        "crop": {"enabled": False, "x": 0, "y": 0, "width": 100, "height": 100},
        "resize": {"enabled": True, "width": 80, "height": 80, "resample": "lanczos"},
    }

    with pytest.raises(ValueError):
        enforce_no_geometry_change_policy(safety, geometry)
