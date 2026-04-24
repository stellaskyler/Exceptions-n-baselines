STATE_MAPPING = {
    "new": "none",
    "triaged": "none",
    "awaiting_approval": "draft",
    "approved_pending_github": "submitted",
    "awaiting_github_merge": "submitted",
    "implemented_active": "active",
    "renewal_due": "active",
    "expired": "expired",
    "revoked": "revoked",
    "closed": "expired",
}


def to_github_state(servicenow_state: str) -> str:
    return STATE_MAPPING.get(servicenow_state, "none")
