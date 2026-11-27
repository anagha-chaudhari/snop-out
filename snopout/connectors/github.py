"""GitHub connector: lists the public repositories of a user or organization."""

from typing import Any

import requests

from snopout.config import get_github_token
from snopout.connectors.base import BaseConnector
from snopout.models import Record
from snopout.connectors.errors import ConnectorError, error_from_status

BASE_URL = "https://api.github.com"
TIMEOUT_SECONDS = (5, 15)  # (connect, read) timeouts in seconds


class GitHubConnector(BaseConnector):
    name = "github"

    def __init__(self, owner: str, per_page: int = 30) -> None:
        self._owner = owner
        self._per_page = per_page
        self._session = requests.Session()

    def authenticate(self) -> None:
        self._session.headers["Accept"] = "application/vnd.github+json"
        token = get_github_token()
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

    def fetch_page(self, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        page = 1 if cursor is None else int(cursor)
        try:
            response = self._session.get(
                f"{BASE_URL}/users/{self._owner}/repos",
                params={"per_page": self._per_page, "page": page},
                timeout=TIMEOUT_SECONDS,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            raise ConnectorError(f"network error (retryable): {exc}", retryable=True) from exc

        if response.status_code != 200:
            raise error_from_status(response.status_code, response.text)

        items = response.json()
        next_cursor = str(page + 1) if "next" in response.links else None
        return items, next_cursor

    def transform(self, raw: dict[str, Any]) -> Record:
        return Record(
            connector=self.name,
            external_id=str(raw["id"]),
            payload={
                "full_name": raw["full_name"],
                "language": raw["language"],
                "stars": raw["stargazers_count"],
                "open_issues": raw["open_issues_count"],
            },
            updated_at=raw["updated_at"],
        )


if __name__ == "__main__":
    connector = GitHubConnector("psf", per_page=10)
    connector.authenticate()
    cursor, total = None, 0
    while True:
        items, cursor = connector.fetch_page(cursor)
        total += len(items)
        print(f"fetched {len(items)} repos, next_cursor={cursor}")
        if cursor is None:
            break
    print("total repos:", total)
    print(connector.transform(items[0]))