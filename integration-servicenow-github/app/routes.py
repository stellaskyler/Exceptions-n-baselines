from __future__ import annotations

from pathlib import Path

from .github_client import MockGitHubClient
from .idempotency_store import FileIdempotencyStore
from .models import Correlation


STORE = FileIdempotencyStore(Path('.cache/idempotency.json'))
GH = MockGitHubClient()


def sync_exception(payload: dict) -> dict:
    key = payload["idempotency_key"]
    existing = STORE.get(key)
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
    )
    STORE.put(key, correlation)
    return {"status": "created", "correlation": correlation.__dict__}
