from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


class RetryError(Exception):
    pass


def with_retries(
    action: Callable[[], T],
    *,
    attempts: int,
    initial_delay_seconds: float,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except retryable_exceptions as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(initial_delay_seconds * (2 ** (attempt - 1)))
    raise RetryError(f"operation failed after {attempts} attempts") from last_error
