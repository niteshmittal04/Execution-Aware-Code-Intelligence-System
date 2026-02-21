from collections.abc import Callable
from time import sleep
from typing import TypeVar

T = TypeVar("T")


def retry_call(
    fn: Callable[[], T],
    attempts: int,
    initial_backoff_seconds: float,
    multiplier: float,
) -> T:
    current_backoff = initial_backoff_seconds
    latest_exception: Exception | None = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            latest_exception = exc
            sleep(current_backoff)
            current_backoff *= multiplier
    if latest_exception is None:
        raise RuntimeError("Retry call failed without exception details.")
    raise latest_exception
