from __future__ import annotations

from datetime import date
from pathlib import Path
import yaml


def _in_rollout(baseline: dict, now: date) -> bool:
    rollout = baseline.get("rollout", {})
    effective_from = rollout.get("effective_from")
    if not effective_from:
        return True
    return now >= date.fromisoformat(str(effective_from))


def _scope_matches(scope: dict, asset: dict) -> bool:
    asset_types = set(scope.get("asset_types", []))
    if asset_types and asset.get("asset_type") not in asset_types:
        return False

    env_in = set(scope.get("env_in", []))
    if env_in and asset.get("environment") not in env_in:
        return False

    required_tags = set(scope.get("tags_all", []))
    asset_tags = set(asset.get("tags", []))
    return required_tags.issubset(asset_tags)


def resolve_required_controls(asset: dict, baseline_dir: Path, now: date | None = None) -> list[str]:
    now = now or date.today()
    required: list[str] = []
    for file in sorted([*baseline_dir.glob("*.yaml"), *baseline_dir.glob("*.yml")]):
        baseline = yaml.safe_load(file.read_text())
        if baseline.get("status") != "approved":
            continue
        if not _in_rollout(baseline, now):
            continue
        if not _scope_matches(baseline.get("scope", {}), asset):
            continue
        for c in baseline.get("controls", []):
            if c.get("required"):
                required.append(c["control_id"])
    return sorted(set(required))
