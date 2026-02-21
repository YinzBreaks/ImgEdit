from __future__ import annotations

from pathlib import Path

from .types import ManifestEntry


def append_manifest_entry(manifest_path: str | Path, entry: ManifestEntry) -> None: ...
