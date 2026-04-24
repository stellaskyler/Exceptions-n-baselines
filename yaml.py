"""Minimal YAML compatibility layer for this repository.

Supports JSON-formatted YAML documents used by this scaffold.
"""

from __future__ import annotations

import json
from typing import Any


def safe_load(data: str) -> Any:
    if not data or not data.strip():
        return None
    return json.loads(data)


def safe_dump(obj: Any, sort_keys: bool = False) -> str:
    return json.dumps(obj, indent=2, sort_keys=sort_keys)
