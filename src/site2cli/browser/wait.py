"""Rich wait conditions for browser automation."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from playwright.async_api import Page


async def _poll_until(
    check: Callable[[], object],
    timeout_ms: int,
    interval_ms: int = 200,
) -> bool:
    """Poll a callable until it returns truthy or timeout expires."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        try:
            if await check() if asyncio.iscoroutinefunction(check) else check():
                return True
        except Exception:
            pass
        await asyncio.sleep(interval_ms / 1000.0)
    return False


async def wait_for_condition(page: Page, condition: str, timeout_ms: int = 30000) -> bool:
    """Wait for a rich condition on the page.

    Supported conditions:
        - network-idle: Wait for network idle state.
        - load: Wait for load event.
        - domcontentloaded: Wait for DOMContentLoaded event.
        - exists:<selector>: Wait for element to exist.
        - visible:<selector>: Wait for element to be visible.
        - hidden:<selector>: Wait for element to be hidden.
        - url-contains:<text>: Wait until page URL contains text.
        - text-contains:<text>: Wait for text to appear on page.
        - stable: Wait until accessibility snapshot stops changing.

    Returns:
        True if condition was met, False if timed out.

    Raises:
        ValueError: If condition is not recognized.
    """
    try:
        if condition == "network-idle":
            await page.wait_for_load_state("networkidle", timeout=timeout_ms)
            return True
        elif condition == "load":
            await page.wait_for_load_state("load", timeout=timeout_ms)
            return True
        elif condition == "domcontentloaded":
            await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            return True
        elif condition.startswith("exists:"):
            selector = condition[len("exists:"):]
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        elif condition.startswith("visible:"):
            selector = condition[len("visible:"):]
            await page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
            return True
        elif condition.startswith("hidden:"):
            selector = condition[len("hidden:"):]
            await page.wait_for_selector(selector, state="hidden", timeout=timeout_ms)
            return True
        elif condition.startswith("url-contains:"):
            text = condition[len("url-contains:"):]
            return await _poll_until(lambda: text in page.url, timeout_ms)
        elif condition.startswith("text-contains:"):
            text = condition[len("text-contains:"):]
            await page.wait_for_selector(f"text={text}", timeout=timeout_ms)
            return True
        elif condition == "stable":
            return await _wait_for_stable(page, timeout_ms)
        else:
            raise ValueError(f"Unknown wait condition: {condition}")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        return False


async def _wait_for_stable(page: Page, timeout_ms: int, interval_ms: int = 500) -> bool:
    """Wait until the accessibility snapshot hash stops changing."""
    prev_hash = ""
    stable_count = 0
    deadline = time.monotonic() + timeout_ms / 1000.0

    while time.monotonic() < deadline:
        try:
            snapshot = await page.accessibility.snapshot()
            current_hash = hashlib.sha256(
                json.dumps(snapshot, sort_keys=True, default=str).encode()
            ).hexdigest()
        except Exception:
            current_hash = ""

        if current_hash == prev_hash and current_hash:
            stable_count += 1
            if stable_count >= 2:
                return True
        else:
            stable_count = 0
        prev_hash = current_hash
        await asyncio.sleep(interval_ms / 1000.0)

    return False
