from __future__ import annotations

from datetime import datetime, timezone
import hashlib


class MockGitHubClient:
    def create_exception_pr(self, exception_request_id: str, version: int) -> dict:
        digest = hashlib.sha1(f"{exception_request_id}:{version}".encode("utf-8")).hexdigest()
        pr_number = 200 + (int(digest[:6], 16) % 8000)
        branch = f"exceptions/{exception_request_id.lower()}-v{version}"
        return {
            "pr_number": pr_number,
            "pr_url": f"https://github.com/org-governance/exception-registry/pull/{pr_number}",
            "branch": branch,
            "record_id": f"EXR-{datetime.now(timezone.utc).year}-{pr_number:06d}",
        }
