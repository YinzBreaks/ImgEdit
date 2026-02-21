from pathlib import Path

import numpy as np
from PIL import Image

from src.pipeline.geometry import assert_geometry_unchanged
from src.pipeline.io import load_image


def test_exif_transpose_disabled_no_geometry_change() -> None:
    arr = np.zeros((2, 3, 3), dtype=np.uint8)
    arr[0, 0] = [255, 0, 0]
    arr[1, 2] = [0, 255, 0]

    path = Path("tests_exif_tmp.png")
    try:
        exif = Image.Exif()
        exif[274] = 6  # Orientation tag: rotate 90 CW when applied
        Image.fromarray(arr, mode="RGB").save(path, format="PNG", exif=exif)

        loaded_no_transpose, _ = load_image(path, apply_exif_transpose=False)
        assert loaded_no_transpose.shape == arr.shape
        assert np.array_equal(loaded_no_transpose, arr)
        assert_geometry_unchanged(arr, loaded_no_transpose)

        loaded_transpose, _ = load_image(path, apply_exif_transpose=True)
        assert loaded_transpose.shape != arr.shape
    finally:
        if path.exists():
            path.unlink()
