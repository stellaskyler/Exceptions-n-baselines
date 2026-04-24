from datetime import date
from pathlib import Path
import json
import sys

sys.path.insert(0, 'policy-engine')
from app.resolver import resolve_required_controls


def test_resolve_required_controls_matches_asset_scope(tmp_path: Path) -> None:
    baseline = {
        'baseline_id': 'BL-TEST',
        'name': 'test',
        'version': '1.0',
        'status': 'approved',
        'scope': {'asset_types': ['repo'], 'tags_all': ['regulated'], 'env_in': ['prod']},
        'controls': [{'control_id': 'CTRL-A', 'required': True}],
        'rollout': {'effective_from': '2026-01-01'},
    }
    file = tmp_path / 'b.yaml'
    file.write_text(json.dumps(baseline))
    asset = {'asset_type': 'repo', 'tags': ['regulated'], 'environment': 'prod'}
    controls = resolve_required_controls(asset, tmp_path, now=date(2026, 4, 24))
    assert controls == ['CTRL-A']
