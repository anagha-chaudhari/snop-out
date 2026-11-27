import logging
import random
import time
from typing import Any, Callable

from snopout.connectors.errors import ConnectorError

logger = logging.getLogger(__name__)

"""Retry helper: exponential backoff with jitter for retryable connector errors."""
""" 3 rules it follows:
- wait longer each time
- wait a random amount
- don't try forever. """

def backoff_ceiling(attempt: int, base_delay: float = 1.0, max_delay: float = 30.0) -> float:
    return min(max_delay, base_delay * 2 ** (attempt - 1))


def with_retry(
    func: Callable[[], Any],
    max_attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    """Call func(). Retry on retryable ConnectorErrors, waiting longer each time."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except ConnectorError as exc:
            if not exc.retryable or attempt == max_attempts:
                raise
            delay = random.uniform(0, backoff_ceiling(attempt, base_delay, max_delay))
            logger.warning("attempt %d/%d failed: %s | retrying in %.2fs", attempt, max_attempts, exc, delay)
            sleep(delay)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print("ceilings:", [backoff_ceiling(n) for n in range(1, 7)])

    calls = {"count": 0}

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise ConnectorError("HTTP 503", 503, retryable=True)
        return "ok"

    waited: list[float] = []
    print("result:", with_retry(flaky, sleep=waited.append))
    print("calls:", calls["count"], "| waits recorded:", len(waited))