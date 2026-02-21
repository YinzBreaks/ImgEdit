from __future__ import annotations

import re


def slugify(value: str, *, fallback: str = "value") -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return clean or fallback
