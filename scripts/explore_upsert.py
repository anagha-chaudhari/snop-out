# upsert and transactions

import json
import sqlite3

print("sqlite library version:", sqlite3.sqlite_version)

conn = sqlite3.connect(":memory:")
conn.execute(
    "CREATE TABLE records ("
    "id INTEGER PRIMARY KEY, connector TEXT NOT NULL, external_id TEXT NOT NULL, "
    "payload TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE (connector, external_id))"
)

UPSERT = (
    "INSERT INTO records (connector, external_id, payload, updated_at) VALUES (?, ?, ?, ?) "
    "ON CONFLICT (connector, external_id) DO UPDATE SET "
    "payload = excluded.payload, updated_at = excluded.updated_at"
)


def row(external_id: str, stars: int, updated_at: str | None) -> tuple:
    return ("github", external_id, json.dumps({"stars": stars}), updated_at)


def show(label: str) -> None:
    count = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    stars = [json.loads(p)["stars"] for (p,) in conn.execute("SELECT payload FROM records ORDER BY external_id")]
    print(f"{label}: {count} rows, stars={stars}")


# the same data twice. The count must not grow.
with conn:
    conn.execute(UPSERT, row("1", 100, "2026-11-01T00:00:00Z"))
show("after run 1")
with conn:
    conn.execute(UPSERT, row("1", 100, "2026-11-01T00:00:00Z"))
show("after run 2 (same data)")

# the item changed at the source. The row must update.
with conn:
    conn.execute(UPSERT, row("1", 150, "2026-11-05T00:00:00Z"))
show("after run 3 (stars changed)")

# a whole page at once: one changed-or-same item and two new ones.
page = [row("1", 150, "2026-11-05T00:00:00Z"), row("2", 20, "2026-11-05T00:00:00Z"), row("3", 30, "2026-11-05T00:00:00Z")]
with conn:
    conn.executemany(UPSERT, page)
show("after page of 3")

# a page where the second row is broken (updated_at is None). All-or-nothing.
bad_page = [row("4", 40, "2026-11-05T00:00:00Z"), row("5", 50, None)]
try:
    with conn:
        conn.executemany(UPSERT, bad_page)
except sqlite3.IntegrityError as exc:
    print("page failed:", exc)
show("after failed page")

# manual control. Insert, look inside the open transaction, then roll back.
conn.execute(UPSERT, row("9", 90, "2026-11-05T00:00:00Z"))
print("inside open transaction:", conn.in_transaction)
conn.rollback()
show("after manual rollback")