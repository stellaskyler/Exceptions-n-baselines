from datetime import date
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
import yaml

spec = spec_from_file_location('exception_store', 'policy-engine/app/exception_store.py')
exception_store = module_from_spec(spec)
spec.loader.exec_module(exception_store)


def test_expired_exception_not_loaded(tmp_path: Path) -> None:
    record = {
        'exception_id': 'EX-000001',
        'asset_id': 'ASSET-1',
        'control_ids': ['CTRL-A'],
        'state': 'active',
        'valid_until': '2026-04-01',
    }
    p = tmp_path / 'e.yaml'
    p.write_text(yaml.safe_dump(record))
    assert exception_store.load_active_exceptions(tmp_path, 'ASSET-1', now=date(2026, 4, 24)) == {}
