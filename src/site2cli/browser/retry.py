"""Generic async retry utility for browser actions."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


async def with_retry(
    action: Callable[[], Awaitable[T]],
    retries: int = 2,
    delay_ms: int = 1000,
    on_retry: Callable[[int, Exception], Awaitable[None]] | None = None,
) -> T:
    """Execute an async action with retry logic.

    Args:
        action: Async callable to execute.
        retries: Number of retry attempts after the first failure.
        delay_ms: Delay between retries in milliseconds.
        on_retry: Optional callback invoked before each retry with (attempt, exception).

    Returns:
        The result of the action.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(1 + retries):
        try:
            return await action()
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                if on_retry:
                    await on_retry(attempt + 1, exc)
                await asyncio.sleep(delay_ms / 1000.0)
    raise last_exc  # type: ignore[misc]
