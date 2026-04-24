def check(sn_state: str, gh_state: str) -> bool:
    return not (gh_state in {"expired", "revoked"} and sn_state == "implemented_active")
