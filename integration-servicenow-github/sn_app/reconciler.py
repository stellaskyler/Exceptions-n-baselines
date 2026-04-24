from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

from .checks import expired_mismatch, field_drift, missing_pr, stale_sn_status
from .state_mapper import to_github_state


@dataclass
class ReconciliationResult:
    missing_pr: int
    stale_sn_status: int
    expired_mismatch: int
    field_drift: int


def reconcile_records(records: list[dict[str, Any]]) -> ReconciliationResult:
    missing_pr_count = 0
    stale_sn_status_count = 0
    expired_mismatch_count = 0
    field_drift_count = 0

    for record in records:
        github = record.get("github", {})
        servicenow = record.get("servicenow", {})
        drift_fields = record.get("drift_fields", ["valid_until", "control_ids", "state"])

        if not missing_pr.check(record):
            missing_pr_count += 1

        sn_state = str(servicenow.get("state", ""))
        gh_state = str(github.get("state", ""))
        expected_gh_state = to_github_state(sn_state)
        normalized_gh_state = gh_state or expected_gh_state

        if not stale_sn_status.check(sn_state, normalized_gh_state):
            stale_sn_status_count += 1

        if not expired_mismatch.check(sn_state, normalized_gh_state):
            expired_mismatch_count += 1

        if field_drift.check(servicenow, github, drift_fields):
            field_drift_count += 1

    return ReconciliationResult(
        missing_pr=missing_pr_count,
        stale_sn_status=stale_sn_status_count,
        expired_mismatch=expired_mismatch_count,
        field_drift=field_drift_count,
    )


def _load_snapshot_records(snapshot_path: Path) -> list[dict[str, Any]]:
    if not snapshot_path.exists():
        return []
    payload = json.loads(snapshot_path.read_text())
    return payload.get("records", [])


def run_reconciliation() -> ReconciliationResult:
    snapshot = Path(os.environ.get("RECONCILIATION_SNAPSHOT_PATH", ".cache/reconciliation_snapshot.json"))
    records = _load_snapshot_records(snapshot)
    return reconcile_records(records)
