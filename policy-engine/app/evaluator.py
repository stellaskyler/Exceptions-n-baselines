from __future__ import annotations

from datetime import date
from .models import ControlDecision, EvaluationResult


def evaluate_controls(asset_id: str, required_controls: list[str], check_results: dict[str, bool], active_exceptions: dict[str, dict], now: date | None = None) -> EvaluationResult:
    now = now or date.today()
    decisions: list[ControlDecision] = []
    for control_id in required_controls:
        passed = bool(check_results.get(control_id, False))
        if passed:
            decisions.append(ControlDecision(control_id=control_id, passed=True, waived=False, reason="control_passed"))
            continue

        if control_id in active_exceptions:
            decisions.append(ControlDecision(control_id=control_id, passed=False, waived=True, reason=f"waived_by:{active_exceptions[control_id].get('exception_id')}"))
            continue

        decisions.append(ControlDecision(control_id=control_id, passed=False, waived=False, reason="control_failed"))
    return EvaluationResult(asset_id=asset_id, decisions=decisions, evaluated_on=now)
