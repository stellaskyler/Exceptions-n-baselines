from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class TTLCache(Generic[T]):
    value: T | None = None
    expires_at: datetime | None = None

    def get(self) -> T | None:
        if self.expires_at and datetime.utcnow() <= self.expires_at:
            return self.value
        return None

    def set(self, value: T, ttl_seconds: int = 60) -> None:
        self.value = value
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
