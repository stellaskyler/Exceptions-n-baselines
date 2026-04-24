from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json
import os
import tempfile

from .models import Correlation


class FileIdempotencyStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(f"{self.path.suffix}.lock")
        self.lock_path.touch(exist_ok=True)
        if not self.path.exists():
            self._atomic_write({})

    def _load(self) -> dict[str, dict]:
        return json.loads(self.path.read_text())

    def _atomic_write(self, data: dict[str, dict]) -> None:
        with tempfile.NamedTemporaryFile('w', dir=self.path.parent, delete=False) as tmp:
            tmp.write(json.dumps(data, indent=2))
            temp_name = tmp.name
        os.replace(temp_name, self.path)

    def _with_lock(self, fn):
        import fcntl

        with self.lock_path.open('r+') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                return fn()
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def get(self, key: str) -> Correlation | None:
        def _read() -> Correlation | None:
            data = self._load()
            if key not in data:
                return None
            return Correlation(**data[key])

        return self._with_lock(_read)

    def put(self, key: str, correlation: Correlation) -> None:
        def _write() -> None:
            data = self._load()
            data[key] = asdict(correlation)
            self._atomic_write(data)

        self._with_lock(_write)
