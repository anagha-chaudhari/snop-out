"""Errors raised by connectors. The flag tells retry logic whether trying again can help."""

class ConnectorError(Exception):
    # A call to a source API failed

    def __init__(self, message: str, status_code: int | None = None, retryable: bool = False) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


def error_from_status(status_code: int, body: str) -> ConnectorError:
    # Build a ConnectorError from a non-200 HTTP response.
    retryable = status_code == 429 or status_code >= 500
    label = "retryable" if retryable else "not retryable"
    return ConnectorError(f"HTTP {status_code} ({label}): {body[:200]}", status_code, retryable)