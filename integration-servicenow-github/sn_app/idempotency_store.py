from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from .models import Correlation


class FileIdempotencyStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")

    def get(self, key: str) -> Correlation | None:
        data = json.loads(self.path.read_text())
        if key not in data:
            return None
        return Correlation(**data[key])

    def put(self, key: str, correlation: Correlation) -> None:
        data = json.loads(self.path.read_text())
        data[key] = asdict(correlation)
        self.path.write_text(json.dumps(data, indent=2))
