"""Tests for browser retry utility."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from site2cli.browser.retry import with_retry


@pytest.mark.asyncio
async def test_success_on_first_try():
    """Action succeeds immediately without retries."""
    action = AsyncMock(return_value="ok")
    result = await with_retry(action, retries=2)
    assert result == "ok"
    assert action.call_count == 1


@pytest.mark.asyncio
async def test_success_after_failure():
    """Action fails once then succeeds."""
    action = AsyncMock(side_effect=[ValueError("fail"), "ok"])
    result = await with_retry(action, retries=2, delay_ms=10)
    assert result == "ok"
    assert action.call_count == 2


@pytest.mark.asyncio
async def test_exhausted_retries_raises():
    """All retries exhausted raises the last exception."""
    action = AsyncMock(side_effect=ValueError("always fails"))
    with pytest.raises(ValueError, match="always fails"):
        await with_retry(action, retries=2, delay_ms=10)
    assert action.call_count == 3  # 1 initial + 2 retries


@pytest.mark.asyncio
async def test_delay_applied(monkeypatch):
    """Delay is applied between retries."""
    sleep_calls: list[float] = []

    async def mock_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    action = AsyncMock(side_effect=[ValueError("fail"), "ok"])
    result = await with_retry(action, retries=2, delay_ms=500)
    assert result == "ok"
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_on_retry_callback():
    """on_retry callback is called with attempt number and exception."""
    callback_args: list[tuple] = []

    async def on_retry(attempt, exc):
        callback_args.append((attempt, str(exc)))

    action = AsyncMock(side_effect=[ValueError("err1"), TypeError("err2"), "ok"])
    result = await with_retry(action, retries=3, delay_ms=10, on_retry=on_retry)
    assert result == "ok"
    assert len(callback_args) == 2
    assert callback_args[0] == (1, "err1")
    assert callback_args[1] == (2, "err2")


@pytest.mark.asyncio
async def test_retries_zero():
    """retries=0 means no retries — action runs once."""
    action = AsyncMock(side_effect=ValueError("fail"))
    with pytest.raises(ValueError, match="fail"):
        await with_retry(action, retries=0, delay_ms=10)
    assert action.call_count == 1


@pytest.mark.asyncio
async def test_returns_correct_type():
    """Return value type is preserved."""
    action = AsyncMock(return_value={"key": "value"})
    result = await with_retry(action)
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_different_exception_types():
    """Different exception types on retries — last one is raised."""
    action = AsyncMock(side_effect=[ValueError("v"), TypeError("t")])
    with pytest.raises(TypeError, match="t"):
        await with_retry(action, retries=1, delay_ms=10)
