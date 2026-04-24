import sys

sys.path.insert(0, 'integration-servicenow-github')
from sn_app.state_mapper import to_github_state


def test_state_mapping_active() -> None:
    assert to_github_state('implemented_active') == 'active'
