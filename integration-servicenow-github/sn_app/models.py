from dataclasses import dataclass


@dataclass
class Correlation:
    exception_request_id: str
    version: int
    pull_request_url: str
    exception_record_id: str
    github_state: str = "submitted"
