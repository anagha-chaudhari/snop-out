"""Basic-auth connector: 
- talks to httpbin.org, 
- a public service for testing HTTP clients."""

from datetime import datetime, timezone
from typing import Any

import requests

from snopout.connectors.base import BaseConnector
from snopout.connectors.errors import ConnectorError, error_from_status
from snopout.models import Record

BASE_URL = "https://httpbin.org"
TIMEOUT = (5, 15)  # (connect seconds, read seconds)


class BasicAuthConnector(BaseConnector):
    name = "basic_auth"

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._session = requests.Session()

    def authenticate(self) -> None:
        self._session.auth = (self._username, self._password)

    def fetch_page(self, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        try:
            response = self._session.get(f"{BASE_URL}/basic-auth/user/pass", timeout=TIMEOUT)
        except (requests.Timeout, requests.ConnectionError) as exc:
            raise ConnectorError(f"network error (retryable): {exc}", retryable=True) from exc

        if response.status_code != 200:
            raise error_from_status(response.status_code, response.text)

        return [response.json()], None  # one item, and no next page

    def transform(self, raw: dict[str, Any]) -> Record:
        return Record(
            connector=self.name,
            external_id=str(raw["user"]),
            payload=raw,
            updated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


if __name__ == "__main__":
    good = BasicAuthConnector("user", "pass")
    good.authenticate()
    items, cursor = good.fetch_page(None)
    print(items, cursor)
    print(good.transform(items[0]))

    bad = BasicAuthConnector("user", "wrong")
    bad.authenticate()
    try:
        bad.fetch_page(None)
    except ConnectorError as exc:
        print("caught:", exc)