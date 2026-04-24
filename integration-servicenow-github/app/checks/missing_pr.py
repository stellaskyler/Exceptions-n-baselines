def check(record: dict) -> bool:
    return bool(record.get("github", {}).get("pull_request_url"))
