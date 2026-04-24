import sys

sys.path.insert(0, 'integration-servicenow-github')
from sn_app.main import post_reconcile_run


def test_reconciliation_returns_expected_shape() -> None:
    result = post_reconcile_run()
    assert set(result.keys()) == {'missing_pr', 'stale_sn_status', 'expired_mismatch', 'field_drift'}
