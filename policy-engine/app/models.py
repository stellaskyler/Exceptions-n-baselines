from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ControlDecision:
    control_id: str
    passed: bool
    waived: bool
    reason: str


@dataclass(frozen=True)
class EvaluationResult:
    asset_id: str
    decisions: list[ControlDecision]
    evaluated_on: date

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "evaluated_on": self.evaluated_on.isoformat(),
            "decisions": [d.__dict__ for d in self.decisions],
            "all_required_pass": all(d.passed or d.waived for d in self.decisions),
        }
