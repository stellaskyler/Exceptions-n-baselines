import sys

sys.path.insert(0, 'integration-servicenow-github')
from sn_app.reconciler import reconcile_records


def test_reconcile_records_counts_each_check() -> None:
    result = reconcile_records(
        [
            {
                'servicenow': {'state': 'implemented_active', 'valid_until': '2026-04-24', 'control_ids': ['CTRL-A']},
                'github': {'state': 'active', 'valid_until': '2026-04-24', 'control_ids': ['CTRL-A'], 'pull_request_url': ''},
            },
            {
                'servicenow': {'state': 'implemented_active', 'valid_until': '2026-04-24', 'control_ids': ['CTRL-A']},
                'github': {'state': 'expired', 'valid_until': '2026-04-30', 'control_ids': ['CTRL-B'], 'pull_request_url': 'https://example/pr/1'},
            },
        ]
    )

    assert result.missing_pr == 1
    assert result.stale_sn_status == 0
    assert result.expired_mismatch == 1
    assert result.field_drift == 2
