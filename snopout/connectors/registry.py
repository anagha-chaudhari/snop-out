"""Connector registry: 
To create a connector by name."""

from typing import Any, Callable

from snopout.connectors.base import BaseConnector
from snopout.connectors.basic_auth import BasicAuthConnector
from snopout.connectors.fake import FakeConnector
from snopout.connectors.github import GitHubConnector

ConnectorFactory = Callable[..., BaseConnector]

_REGISTRY: dict[str, ConnectorFactory] = {}


def register(name: str, factory: ConnectorFactory) -> None:
    # Add a connector class under a name. Names must be unique
    if name in _REGISTRY:
        raise ValueError(f"connector '{name}' is already registered")
    _REGISTRY[name] = factory


def create_connector(name: str, **options: Any) -> BaseConnector:
    # Build the connector registered under `name`, passing options to its constructor
    try:
        factory = _REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown connector '{name}'. Available: {sorted(_REGISTRY)}") from None
    return factory(**options)


def available_connectors() -> list[str]:
    return sorted(_REGISTRY)


register("github", GitHubConnector)
register("basic_auth", BasicAuthConnector)
register("fake", FakeConnector)


if __name__ == "__main__":
    print("available:", available_connectors())
    fake = create_connector("fake", total_items=3)
    print(type(fake).__name__, "| name:", fake.name, "| is BaseConnector:", isinstance(fake, BaseConnector))
    github = create_connector("github", owner="psf", per_page=5)
    print(type(github).__name__, "| name:", github.name)
    try:
        create_connector("slack")
    except ValueError as exc:
        print("caught:", exc)