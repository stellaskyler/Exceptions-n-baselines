from datetime import date
import sys

sys.path.insert(0, 'policy-engine')
from app.evaluator import evaluate_controls


def test_evaluator_waives_failed_control_with_active_exception() -> None:
    result = evaluate_controls(
        asset_id='ASSET-1',
        required_controls=['CTRL-A'],
        check_results={'CTRL-A': False},
        active_exceptions={'CTRL-A': {'exception_id': 'EX-000001'}},
        now=date(2026, 4, 24),
    )
    assert result.to_dict()['all_required_pass'] is True
