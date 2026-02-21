from __future__ import annotations

import json
from pathlib import Path

from .types import ManifestEntry


def append_manifest_entry(manifest_path: str | Path, entry: ManifestEntry) -> None:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with open(path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    else:
        manifest = {"entries": []}

    manifest.setdefault("entries", []).append(entry)

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
