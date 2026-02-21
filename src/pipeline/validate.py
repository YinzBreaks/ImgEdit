from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema(path: str | Path) -> dict:
    return load_json(path)


def load_preset(path: str | Path) -> dict:
    return load_json(path)


def validate_preset(preset: dict, schema: dict) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(preset), key=lambda e: e.path)
    if errors:
        lines = []
        for err in errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            lines.append(f"- {loc}: {err.message}")
        raise ValueError("Preset validation failed:\n" + "\n".join(lines))
