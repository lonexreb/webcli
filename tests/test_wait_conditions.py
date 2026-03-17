"""Tests for rich wait conditions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from site2cli.browser.wait import wait_for_condition


def _make_page():
    """Create a mock Playwright page."""
    page = AsyncMock()
    page.url = "https://example.com/page"
    page.wait_for_load_state = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.accessibility = MagicMock()
    page.accessibility.snapshot = AsyncMock(return_value={"role": "WebArea", "name": "Test"})
    return page


@pytest.mark.asyncio
async def test_network_idle():
    page = _make_page()
    result = await wait_for_condition(page, "network-idle", timeout_ms=1000)
    assert result is True
    page.wait_for_load_state.assert_called_once_with("networkidle", timeout=1000)


@pytest.mark.asyncio
async def test_load():
    page = _make_page()
    result = await wait_for_condition(page, "load", timeout_ms=2000)
    assert result is True
    page.wait_for_load_state.assert_called_once_with("load", timeout=2000)


@pytest.mark.asyncio
async def test_domcontentloaded():
    page = _make_page()
    result = await wait_for_condition(page, "domcontentloaded", timeout_ms=3000)
    assert result is True
    page.wait_for_load_state.assert_called_once_with("domcontentloaded", timeout=3000)


@pytest.mark.asyncio
async def test_exists_selector():
    page = _make_page()
    result = await wait_for_condition(page, "exists:#myid", timeout_ms=1000)
    assert result is True
    page.wait_for_selector.assert_called_once_with("#myid", timeout=1000)


@pytest.mark.asyncio
async def test_visible_selector():
    page = _make_page()
    result = await wait_for_condition(page, "visible:.btn", timeout_ms=1000)
    assert result is True
    page.wait_for_selector.assert_called_once_with(".btn", state="visible", timeout=1000)


@pytest.mark.asyncio
async def test_hidden_selector():
    page = _make_page()
    result = await wait_for_condition(page, "hidden:.modal", timeout_ms=1000)
    assert result is True
    page.wait_for_selector.assert_called_once_with(".modal", state="hidden", timeout=1000)


@pytest.mark.asyncio
async def test_url_contains():
    page = _make_page()
    page.url = "https://example.com/dashboard"
    result = await wait_for_condition(page, "url-contains:dashboard", timeout_ms=500)
    assert result is True


@pytest.mark.asyncio
async def test_text_contains():
    page = _make_page()
    result = await wait_for_condition(page, "text-contains:Hello", timeout_ms=1000)
    assert result is True
    page.wait_for_selector.assert_called_once_with("text=Hello", timeout=1000)


@pytest.mark.asyncio
async def test_timeout_returns_false():
    page = _make_page()
    page.wait_for_load_state = AsyncMock(side_effect=TimeoutError("timed out"))
    result = await wait_for_condition(page, "network-idle", timeout_ms=100)
    assert result is False


@pytest.mark.asyncio
async def test_unknown_condition_raises():
    page = _make_page()
    with pytest.raises(ValueError, match="Unknown wait condition"):
        await wait_for_condition(page, "nonexistent-condition", timeout_ms=100)
