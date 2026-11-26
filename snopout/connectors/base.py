from abc import ABC, abstractmethod
from typing import Any

from snopout.models import Record


class BaseConnector(ABC):
    """Abstract base class. Subclasses fetch data from one source system."""

    name: str 

    @abstractmethod
    def authenticate(self) -> None:
        """Prepare credentials so requests are accepted by the source API."""

    @abstractmethod
    def fetch_page(self, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of raw items."""

    @abstractmethod
    def transform(self, raw: dict[str, Any]) -> Record:
        """Convert one raw item from the source into a standard Record."""