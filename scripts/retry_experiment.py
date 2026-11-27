"""Experiment: how many calls hit by injected failures does with_retry rescue? No network."""

from snopout.connectors.errors import ConnectorError
from snopout.connectors.fake import FakeConnector
from snopout.connectors.faulty import FaultInjector
from snopout.pipeline.retry import with_retry

TRIALS = 1000
FAILURE_RATE = 0.30
MAX_ATTEMPTS = 4


def run(use_retry: bool, status_code: int = 503) -> dict[str, int]:
    connector = FaultInjector(FakeConnector(), FAILURE_RATE, status_code=status_code, seed=42)
    connector.authenticate()
    failed = disrupted = recovered = 0
    for _ in range(TRIALS):
        injected_before = connector.injected
        try:
            if use_retry:
                with_retry(lambda: connector.fetch_page(None), max_attempts=MAX_ATTEMPTS, sleep=lambda s: None)
            else:
                connector.fetch_page(None)
            succeeded = True
        except ConnectorError:
            succeeded = False

        was_hit = connector.injected > injected_before
        if not succeeded:
            failed += 1
        if was_hit:
            disrupted += 1
            if succeeded:
                recovered += 1
    return {"failed": failed, "disrupted": disrupted, "recovered": recovered, "calls": connector.calls}


if __name__ == "__main__":
    print(f"trials={TRIALS} failure_rate={FAILURE_RATE} max_attempts={MAX_ATTEMPTS}")
    print("without retry          :", run(use_retry=False))
    print("with retry (503)       :", run(use_retry=True))
    print("with retry (401, perm.):", run(use_retry=True, status_code=401))