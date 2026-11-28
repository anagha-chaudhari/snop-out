## Rough notes
### 1. Retry Recovery
- python -m scripts.retry_experiment

Setup: simulated failures (HTTP 503, independent), failure rate 30%, 1000 calls, max 4 attempts, seed 42, no network
- Without retry: 295 of 1000 calls failed
- With retry: 285 of 293 disrupted calls recovered; 8 still failed; 1414 total calls made
- Permanent error check (401): total calls = 1000 (no retry on permanent errors)
- Caveat: failures are injected and independent, not from a real API. Real outages are bursty

numbers:

- Recovered 285 of 293 disrupted calls = 97.3%.
- Failed calls fell from 295 to 8, a 97.3% reduction.
- Cost: 414 extra calls (+41.4%). Retries aren't free, and that matters when an API has a rate limit.
- Permanent errors (401): 0 retries.

- in a fault-injection test (1,000 calls, simulated 30% transient 503s), retry with exponential backoff and jitter recovered 285 of 293 affected calls, cutting failed calls from 295 to 8, while 401 errors were correctly not retried


### 2. Idempotent loads (zero duplicates)
- Command: python -m scripts.idempotency_experiment
- Setup: FakeConnector, 500 items per run, 20 reruns, in-memory SQLite, no network
- Control (plain INSERT, no unique rule): 10000 rows after 20 runs, 500 duplicated keys
- Upsert with UNIQUE(connector, external_id): 500 rows after 20 runs, 0 duplicated keys
- Content after 20 reruns identical to run 1: True
- Source edit of 100 items: rows = 500, rows changed = 100
- Caveat: zero duplicates is enforced by the UNIQUE constraint. This experiment verifies the full path (connector, transform, loader, database) and shows the contrast with the control. The source is a fake. Items deleted at the source are not handled

- Verified zero duplicated keys after 20 repeated syncs of 500 items (a plain-INSERT control produced 10,000 rows), while a source edit updated exactly 100 rows in place.