from pathlib import Path
import sys

sys.path.insert(0, 'integration-servicenow-github')
from sn_app.main import post_exceptions_sync


def test_sync_creates_and_then_deduplicates() -> None:
    cache_file = Path('.cache/idempotency.json')
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text('{}')

    payload = {
        'exception_request_id': 'SN-EXC-001',
        'request_state': 'approved_pending_github',
        'idempotency_key': 'SN-EXC-001:v1',
        'version': 1,
    }
    first = post_exceptions_sync(payload)
    second = post_exceptions_sync(payload)
    assert first['status'] == 'created'
    assert second['status'] == 'deduplicated'
