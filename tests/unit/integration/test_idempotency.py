from pathlib import Path
import sys

sys.path.insert(0, 'integration-servicenow-github')
from app.idempotency_store import FileIdempotencyStore
from app.models import Correlation


def test_idempotency_store_roundtrip(tmp_path: Path) -> None:
    store = FileIdempotencyStore(tmp_path / 'idem.json')
    c = Correlation('SN-1', 1, 'https://example/pr/1', 'EXR-2026-000001')
    store.put('SN-1:v1', c)
    got = store.get('SN-1:v1')
    assert got is not None
    assert got.pull_request_url == c.pull_request_url
