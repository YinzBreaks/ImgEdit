from __future__ import annotations

from pathlib import Path
from typing import Any

from .types import ImageU8


def load_image(path: str | Path, *, apply_exif_transpose: bool = False) -> tuple[ImageU8, dict[str, Any]]: ...
def sha256_file(path: str | Path) -> str: ...
def save_image(
	arr: ImageU8,
	path: str | Path,
	fmt: str,
	*,
	quality: int = 92,
	embed_profile: bool = True,
	icc_profile: bytes | None = None,
) -> None: ...
