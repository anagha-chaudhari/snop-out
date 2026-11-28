"""Load Record objects into SQLite with an idempotent upsert."""

import json
import sqlite3
from typing import Iterable

from snopout.models import Record

UPSERT_SQL = (
    "INSERT INTO records (connector, external_id, payload, updated_at) VALUES (?, ?, ?, ?) "
    "ON CONFLICT (connector, external_id) DO UPDATE SET "
    "payload = excluded.payload, updated_at = excluded.updated_at"
)


def upsert_records(conn: sqlite3.Connection, records: Iterable[Record]) -> int:
    rows = [(r.connector, r.external_id, json.dumps(r.payload, sort_keys=True), r.updated_at) for r in records]
    with conn:
        conn.executemany(UPSERT_SQL, rows)
    return len(rows)


def count_records(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]


if __name__ == "__main__":
    from snopout.db.schema import get_connection, init_db

    conn = get_connection(":memory:")
    init_db(conn)
    batch = [Record("fake", str(i), {"title": f"item {i}"}, "2026-11-01T00:00:00Z") for i in (1, 2, 3)]
    upsert_records(conn, batch)
    print("after first load:", count_records(conn), "rows")
    upsert_records(conn, batch)
    print("after second load (same data):", count_records(conn), "rows")

    edited = Record("fake", "2", {"title": "changed"}, "2026-11-02T00:00:00Z")
    upsert_records(conn, [edited])
    row = conn.execute("SELECT payload FROM records WHERE external_id = ?", ("2",)).fetchone()
    print("after edit:", count_records(conn), "rows | item 2 payload =", row["payload"])

    bad = [Record("fake", "7", {}, "2026-11-01T00:00:00Z"), Record("fake", "8", {}, None)]  # None is wrong on purpose
    try:
        upsert_records(conn, bad)
    except sqlite3.IntegrityError as exc:
        print("bad batch rejected:", exc)
    print("after bad batch:", count_records(conn), "rows")