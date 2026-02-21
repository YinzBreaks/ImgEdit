from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema(path: str | Path) -> dict[str, Any]:
    return load_json(path)


def load_preset(path: str | Path) -> dict[str, Any]:
    return load_json(path)


def validate_preset(preset: dict[str, Any], schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(preset), key=lambda e: e.path)
    if errors:
        lines = []
        for err in errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            lines.append(f"- {loc}: {err.message}")
        raise ValueError("Preset validation failed:\n" + "\n".join(lines))
