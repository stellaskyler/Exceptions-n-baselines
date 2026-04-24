from __future__ import annotations

from pathlib import Path
import os

from .github_client import MockGitHubClient
from .idempotency_store import FileIdempotencyStore
from .models import Correlation
from .state_mapper import to_github_state


IDEMPOTENCY_STORE_PATH = Path(os.environ.get('IDEMPOTENCY_STORE_PATH', '.cache/idempotency.json'))
STORE = FileIdempotencyStore(IDEMPOTENCY_STORE_PATH)
GH = MockGitHubClient()


def sync_exception(payload: dict, store: FileIdempotencyStore | None = None) -> dict:
    store = store or STORE
    if payload.get("request_state") != "approved_pending_github":
        raise ValueError("request_state must be approved_pending_github to create a GitHub exception PR")

    key = payload["idempotency_key"]
    existing = store.get(key)
    if existing:
        return {"status": "deduplicated", "correlation": existing.__dict__}

    request_id = payload["exception_request_id"]
    version = int(payload.get("version", 1))
    created = GH.create_exception_pr(request_id, version)
    correlation = Correlation(
        exception_request_id=request_id,
        version=version,
        pull_request_url=created["pr_url"],
        exception_record_id=created["record_id"],
        github_state=to_github_state(payload.get("request_state", "")),
    )
    store.put(key, correlation)
    return {"status": "created", "correlation": correlation.__dict__}
