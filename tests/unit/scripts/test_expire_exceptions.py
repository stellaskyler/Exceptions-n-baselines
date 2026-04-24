from datetime import date
from pathlib import Path

import yaml

from scripts.expire_exceptions import expire_exceptions


def test_expire_exceptions_skips_invalid_or_missing_valid_until(tmp_path: Path) -> None:
    missing = tmp_path / 'missing.yaml'
    invalid = tmp_path / 'invalid.yaml'
    valid = tmp_path / 'valid.yaml'

    missing.write_text(yaml.safe_dump({'state': 'active'}))
    invalid.write_text(yaml.safe_dump({'state': 'active', 'valid_until': 'not-a-date'}))
    valid.write_text(yaml.safe_dump({'state': 'active', 'valid_until': '2026-01-01'}))

    expired, skipped = expire_exceptions(tmp_path, date(2026, 4, 24))

    assert expired == [valid]
    assert len(skipped) == 2
    assert 'missing valid_until' in skipped[0] or 'missing valid_until' in skipped[1]
    assert 'invalid valid_until' in skipped[0] or 'invalid valid_until' in skipped[1]

    persisted = yaml.safe_load(valid.read_text())
    assert persisted['state'] == 'expired'
