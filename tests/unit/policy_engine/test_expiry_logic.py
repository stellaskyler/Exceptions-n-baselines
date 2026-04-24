from datetime import date
from pathlib import Path
import json
import sys

sys.path.insert(0, 'policy-engine')
from app.exception_store import load_active_exceptions


def test_expired_exception_not_loaded(tmp_path: Path) -> None:
    record = {
        'exception_id': 'EX-000001',
        'asset_id': 'ASSET-1',
        'control_ids': ['CTRL-A'],
        'state': 'active',
        'valid_until': '2026-04-01',
    }
    p = tmp_path / 'e.yaml'
    p.write_text(json.dumps(record))
    assert load_active_exceptions(tmp_path, 'ASSET-1', now=date(2026, 4, 24)) == {}
