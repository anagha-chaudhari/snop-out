"""A fake connector with no network. Proves the BaseConnector rulebook works."""

from typing import Any

from snopout.connectors.base import BaseConnector
from snopout.models import Record

PAGE_SIZE = 2


class FakeConnector(BaseConnector):
    name = "fake"

    def __init__(self, total_items: int = 5) -> None:
        self._items = [{"id": i, "title": f"item {i}"} for i in range(1, total_items + 1)]
        self.authenticated = False

    def authenticate(self) -> None:
        self.authenticated = True

    def fetch_page(self, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        start = 0 if cursor is None else int(cursor)
        end = start + PAGE_SIZE
        items = self._items[start:end]
        next_cursor = str(end) if end < len(self._items) else None
        return items, next_cursor

    def transform(self, raw: dict[str, Any]) -> Record:
        return Record(
            connector=self.name,
            external_id=str(raw["id"]),
            payload={"title": raw["title"]},
            updated_at="2026-11-20T10:00:00",
        )


if __name__ == "__main__":
    connector = FakeConnector()
    connector.authenticate()
    cursor = None
    while True:
        items, cursor = connector.fetch_page(cursor)
        print(f"page of {len(items)} items, next_cursor={cursor}")
        for raw in items:
            print("  ", connector.transform(raw))
        if cursor is None:
            break