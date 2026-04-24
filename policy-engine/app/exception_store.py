from __future__ import annotations

from datetime import date
from pathlib import Path
import yaml


ACTIVE_STATES = {"active"}


def load_active_exceptions(path: Path, asset_id: str, now: date | None = None) -> dict[str, dict]:
    now = now or date.today()
    active: dict[str, dict] = {}
    for file in path.rglob("*.yaml"):
        record = yaml.safe_load(file.read_text())
        if record.get("asset_id") != asset_id:
            continue
        if record.get("state") not in ACTIVE_STATES:
            continue
        if now > date.fromisoformat(str(record["valid_until"])):
            continue
        for control_id in record.get("control_ids", []):
            active[control_id] = record
    return active
