from pathlib import Path
import pytest
import sys

sys.path.insert(0, 'integration-servicenow-github')
from sn_app.routes import sync_exception
from sn_app.idempotency_store import FileIdempotencyStore


def test_sync_exception_rejects_non_approved_state(tmp_path: Path) -> None:
    store = FileIdempotencyStore(tmp_path / 'idem.json')
    with pytest.raises(ValueError):
        sync_exception(
            {
                'exception_request_id': 'SN-EXC-102',
                'request_state': 'awaiting_approval',
                'idempotency_key': 'SN-EXC-102:v1',
                'version': 1,
            },
            store=store,
        )
