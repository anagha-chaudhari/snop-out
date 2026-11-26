"""The common record shape used everywhere in Snopout."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Record:
    connector: str      # which source it came from e.g. "github"
    external_id: str    # the item's ID inside the source system
    payload: dict[str, Any]   # the cleaned data
    updated_at: str    # ISO 8601 time, e.g. "2026-11-20T10:00:00"