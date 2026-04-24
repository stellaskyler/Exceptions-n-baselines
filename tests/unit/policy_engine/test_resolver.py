from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import yaml

spec = spec_from_file_location('resolver', 'policy-engine/app/resolver.py')
resolver = module_from_spec(spec)
spec.loader.exec_module(resolver)


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
    file.write_text(yaml.safe_dump(baseline))
    asset = {'asset_type': 'repo', 'tags': ['regulated'], 'environment': 'prod'}
    controls = resolver.resolve_required_controls(asset, tmp_path, now=date(2026, 4, 24))
    assert controls == ['CTRL-A']
