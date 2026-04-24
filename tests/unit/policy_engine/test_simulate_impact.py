import sys

sys.path.insert(0, 'policy-engine')
from app.main import simulate_impact


def test_simulate_impact_supports_multiple_scenarios() -> None:
    result = simulate_impact(
        {
            'asset_id': 'ASSET-REPO-org-cloud-networking-iac',
            'decision_date': '2026-04-24',
            'scenarios': [
                {'name': 'all-pass', 'check_results': {'CTRL-GH-BRANCH-PROTECT': True, 'CTRL-GH-CODEOWNERS': True, 'CTRL-PR-SECURITY-REVIEW-MANDATORY': True}},
                {'name': 'codeowners-fails', 'check_results': {'CTRL-GH-BRANCH-PROTECT': True, 'CTRL-GH-CODEOWNERS': False, 'CTRL-PR-SECURITY-REVIEW-MANDATORY': True}},
            ],
        }
    )

    assert result['status'] == 'ok'
    assert result['projection_count'] == 2
    assert result['projections'][0]['all_required_pass'] is True
    assert result['projections'][1]['all_required_pass'] is True
    assert result['required_controls'] == []
    assert result['projections'][1]['waived_controls'] == []
