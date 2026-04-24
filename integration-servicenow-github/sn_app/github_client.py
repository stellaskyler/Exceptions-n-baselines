from __future__ import annotations

from datetime import datetime, timezone


class MockGitHubClient:
    def create_exception_pr(self, exception_request_id: str, version: int) -> dict:
        pr_number = 200 + version
        return {
            "pr_number": pr_number,
            "pr_url": f"https://github.com/org-governance/exception-registry/pull/{pr_number}",
            "record_id": f"EXR-{datetime.now(timezone.utc).year}-{pr_number:06d}",
        }
