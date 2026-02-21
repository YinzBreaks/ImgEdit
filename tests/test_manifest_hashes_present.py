import json
from pathlib import Path

from src.pipeline.manifest import append_manifest_entry


def test_manifest_hashes_present(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    entry = {
        "timestamp_utc": "2026-01-01T00:00:00+00:00",
        "input_file": "in/sample.png",
        "input_hash": "abc",
        "preset_file": "presets/x.json",
        "preset_hash": "def",
        "output_files": {"master": "out/x.png"},
        "output_hashes": {"master": "ghi"},
        "report_file": "reports/x.md",
        "versions": {"python": "3.12", "pillow": "10", "numpy": "1", "jsonschema": "4"},
        "settings": {},
    }

    append_manifest_entry(manifest_path, entry)

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "entries" in data
    assert data["entries"][0]["input_hash"]
    assert data["entries"][0]["preset_hash"]
    assert data["entries"][0]["output_hashes"]["master"]
