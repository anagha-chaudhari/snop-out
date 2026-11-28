import json
import sqlite3
from typing import Any, Iterator

from snopout.connectors.base import BaseConnector
from snopout.connectors.fake import FakeConnector
from snopout.db.loader import upsert_records
from snopout.db.schema import get_connection, init_db
from snopout.models import Record

ITEMS = 500
RERUNS = 20


class EditedFake(FakeConnector):
    """Same source, but items 1 to 100 have changed."""

    def transform(self, raw: dict[str, Any]) -> Record:
        record = super().transform(raw)
        if raw["id"] <= 100:
            return Record(record.connector, record.external_id, {"title": raw["title"] + " (edited)"}, "2026-11-02T00:00:00Z")
        return record


def pages(connector: BaseConnector) -> Iterator[list[Record]]:
    """Yield one list of Records per page. A mini version of what the runner (M6) will do."""
    connector.authenticate()
    cursor = None
    while True:
        items, cursor = connector.fetch_page(cursor)
        yield [connector.transform(raw) for raw in items]
        if cursor is None:
            return


def naive_insert(conn: sqlite3.Connection, records: list[Record]) -> None:
    sql = "INSERT INTO naive (connector, external_id, payload, updated_at) VALUES (?, ?, ?, ?)"
    with conn:
        conn.executemany(sql, [(r.connector, r.external_id, json.dumps(r.payload, sort_keys=True), r.updated_at) for r in records])


def count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # table name is a constant of ours


def duplicated_keys(conn: sqlite3.Connection, table: str) -> int:
    sql = f"SELECT COUNT(*) FROM (SELECT 1 FROM {table} GROUP BY connector, external_id HAVING COUNT(*) > 1)"
    return conn.execute(sql).fetchone()[0]


def snapshot(conn: sqlite3.Connection) -> dict[str, str]:
    return {row["external_id"]: row["payload"] for row in conn.execute("SELECT external_id, payload FROM records")}


if __name__ == "__main__":
    conn = get_connection(":memory:")
    init_db(conn)
    conn.execute("CREATE TABLE naive (id INTEGER PRIMARY KEY, connector TEXT, external_id TEXT, payload TEXT, updated_at TEXT)")

    print(f"items per run={ITEMS}, reruns={RERUNS}")
    for run in range(1, RERUNS + 1):
        for page in pages(FakeConnector(ITEMS)):
            naive_insert(conn, page)
            upsert_records(conn, page)
        if run == 1:
            first = snapshot(conn)
            print(f"after run 1:  plain INSERT={count(conn, 'naive')} rows | upsert={count(conn, 'records')} rows")
    print(f"after run {RERUNS}: plain INSERT={count(conn, 'naive')} rows | upsert={count(conn, 'records')} rows")
    print(f"duplicated keys: plain INSERT={duplicated_keys(conn, 'naive')} | upsert={duplicated_keys(conn, 'records')}")
    print("upsert content identical to run 1:", snapshot(conn) == first)

    for page in pages(EditedFake(ITEMS)):
        upsert_records(conn, page)
    after = snapshot(conn)
    changed = sum(1 for key in after if after[key] != first[key])
    print(f"after source edit: rows={count(conn, 'records')} | rows whose content changed={changed}")