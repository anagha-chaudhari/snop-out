import random
from typing import Any

from snopout.connectors.base import BaseConnector
from snopout.connectors.errors import error_from_status
from snopout.models import Record


class FaultInjector(BaseConnector):
    # Wraps another connector and randomly raises errors from fetch_page

    def __init__(self, inner: BaseConnector, failure_rate: float, status_code: int = 503, seed: int = 42) -> None:
        self._inner = inner
        self._failure_rate = failure_rate
        self._status_code = status_code
        self._rng = random.Random(seed)
        self.name = inner.name
        self.calls = 0   # how many times fetch_page was called
        self.injected = 0  # how many failures we caused

    def authenticate(self) -> None:
        self._inner.authenticate()

    def fetch_page(self, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        self.calls += 1
        if self._rng.random() < self._failure_rate:
            self.injected += 1
            raise error_from_status(self._status_code, "injected failure")
        return self._inner.fetch_page(cursor)

    def transform(self, raw: dict[str, Any]) -> Record:
        return self._inner.transform(raw)