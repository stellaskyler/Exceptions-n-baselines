from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
import yaml

from .config import ASSET_DIR, BASELINE_DIR, EXCEPTION_DIR
from .resolver import resolve_required_controls
from .exception_store import load_active_exceptions
from .evaluator import evaluate_controls


def load_asset(asset_id: str) -> dict[str, Any]:
    for file in Path(ASSET_DIR).glob("*.yaml"):
        data = yaml.safe_load(file.read_text())
        if data.get("asset_id") == asset_id:
            return data
    raise FileNotFoundError(f"asset not found: {asset_id}")


def evaluate(request: dict[str, Any]) -> dict[str, Any]:
    asset_id = request["asset_id"]
    now = date.fromisoformat(request.get("decision_date", date.today().isoformat()))
    asset = load_asset(asset_id)
    required_controls = resolve_required_controls(asset, Path(BASELINE_DIR), now=now)
    active_exceptions = load_active_exceptions(Path(EXCEPTION_DIR), asset_id=asset_id, now=now)
    check_results = request.get("check_results", {})
    result = evaluate_controls(asset_id, required_controls, check_results, active_exceptions, now=now)
    return result.to_dict()


def simulate_impact(request: dict[str, Any]) -> dict[str, Any]:
    return {"status": "ok", "request": request}


if __name__ == "__main__":
    sample = {
        "asset_id": "ASSET-REPO-org-cloud-networking-iac",
        "check_results": {
            "CTRL-GH-BRANCH-PROTECT": True,
            "CTRL-GH-CODEOWNERS": False,
            "CTRL-PR-SECURITY-REVIEW-MANDATORY": True,
        },
    }
    print(evaluate(sample))
