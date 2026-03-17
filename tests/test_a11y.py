"""Tests for accessibility tree extraction."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from site2cli.browser.a11y import (
    A11yNode,
    extract_a11y_tree,
    format_a11y_for_llm,
    get_a11y_hash,
)

MOCK_SNAPSHOT = {
    "role": "WebArea",
    "name": "Test Page",
    "children": [
        {
            "role": "heading",
            "name": "Welcome",
            "level": 1,
            "children": [],
        },
        {
            "role": "button",
            "name": "Click me",
            "children": [],
        },
        {
            "role": "textbox",
            "name": "Email",
            "value": "test@example.com",
            "children": [],
        },
        {
            "role": "checkbox",
            "name": "Remember me",
            "checked": True,
            "children": [],
        },
    ],
}


def _make_page(snapshot=None):
    page = AsyncMock()
    page.accessibility = MagicMock()
    page.accessibility.snapshot = AsyncMock(return_value=snapshot or MOCK_SNAPSHOT)
    return page


@pytest.mark.asyncio
async def test_extract_a11y_tree():
    """Parse mock snapshot into A11yNode list."""
    page = _make_page()
    nodes = await extract_a11y_tree(page)
    assert len(nodes) >= 4
    roles = [n.role for n in nodes]
    assert "heading" in roles
    assert "button" in roles
    assert "textbox" in roles


@pytest.mark.asyncio
async def test_a11y_node_fields():
    """A11yNode captures role, name, value, checked."""
    page = _make_page()
    nodes = await extract_a11y_tree(page)
    checkbox = [n for n in nodes if n.role == "checkbox"][0]
    assert checkbox.name == "Remember me"
    assert checkbox.checked is True

    textbox = [n for n in nodes if n.role == "textbox"][0]
    assert textbox.value == "test@example.com"


@pytest.mark.asyncio
async def test_format_truncation():
    """format_a11y_for_llm respects max_items."""
    nodes = [A11yNode(role="button", name=f"btn{i}") for i in range(200)]
    result = format_a11y_for_llm(nodes, max_items=10)
    lines = result.strip().split("\n")
    # 10 items + 1 "... more" line
    assert len(lines) == 11
    assert "190 more nodes" in lines[-1]


@pytest.mark.asyncio
async def test_format_includes_roles():
    """Formatted output includes role annotations."""
    nodes = [A11yNode(role="button", name="Submit")]
    result = format_a11y_for_llm(nodes)
    assert "[button]" in result
    assert '"Submit"' in result


@pytest.mark.asyncio
async def test_hash_determinism():
    """Same snapshot produces same hash."""
    page = _make_page()
    hash1 = await get_a11y_hash(page)
    hash2 = await get_a11y_hash(page)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex


@pytest.mark.asyncio
async def test_hash_changes_on_content_change():
    """Different snapshots produce different hashes."""
    page1 = _make_page({"role": "WebArea", "name": "Page 1"})
    page2 = _make_page({"role": "WebArea", "name": "Page 2"})
    hash1 = await get_a11y_hash(page1)
    hash2 = await get_a11y_hash(page2)
    assert hash1 != hash2


@pytest.mark.asyncio
async def test_empty_snapshot():
    """Empty snapshot returns empty list."""
    page = _make_page(snapshot=None)
    page.accessibility.snapshot = AsyncMock(return_value=None)
    nodes = await extract_a11y_tree(page)
    assert nodes == []


@pytest.mark.asyncio
async def test_graceful_fallback_on_error():
    """get_a11y_hash returns empty string on error."""
    page = _make_page()
    page.accessibility.snapshot = AsyncMock(side_effect=Exception("fail"))
    result = await get_a11y_hash(page)
    assert result == ""
