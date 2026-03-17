"""Tests for cookie banner detection and dismissal."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from site2cli.browser.cookie_banner import (
    ACCEPT_TEXT_PATTERNS,
    COOKIE_CONTEXT_KEYWORDS,
    VENDOR_SELECTORS,
    CookieBannerResult,
    dismiss_cookie_banner,
)


def _make_page(
    vendor_visible: str | None = None,
    page_text: str = "",
    button_texts: list[str] | None = None,
    a11y_snapshot: dict | None = None,
):
    """Create a mock page with configurable banner state."""
    page = AsyncMock()

    # query_selector for vendor selectors
    async def query_selector(selector):
        if vendor_visible and selector == vendor_visible:
            el = AsyncMock()
            el.is_visible = AsyncMock(return_value=True)
            el.click = AsyncMock()
            return el
        return None

    page.query_selector = query_selector
    page.wait_for_timeout = AsyncMock()

    # evaluate for page text
    page.evaluate = AsyncMock(return_value=page_text)

    # query_selector_all for text matching
    async def query_selector_all(tag):
        if button_texts is None:
            return []
        elements = []
        for text in button_texts:
            el = AsyncMock()
            el.text_content = AsyncMock(return_value=text)
            el.is_visible = AsyncMock(return_value=True)
            el.click = AsyncMock()
            elements.append(el)
        return elements

    page.query_selector_all = query_selector_all

    # accessibility for a11y strategy
    page.accessibility = MagicMock()
    page.accessibility.snapshot = AsyncMock(return_value=a11y_snapshot)
    page.get_by_role = MagicMock()
    if a11y_snapshot:
        role_locator = AsyncMock()
        role_locator.click = AsyncMock()
        page.get_by_role.return_value = role_locator

    return page


@pytest.mark.asyncio
async def test_vendor_selector_onetrust():
    """OneTrust selector detected and dismissed."""
    page = _make_page(vendor_visible="#onetrust-accept-btn-handler")
    result = await dismiss_cookie_banner(page)
    assert result.detected is True
    assert result.dismissed is True
    assert result.method == "vendor_css"


@pytest.mark.asyncio
async def test_vendor_selector_cookiebot():
    """Cookiebot selector detected and dismissed."""
    page = _make_page(vendor_visible="#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
    result = await dismiss_cookie_banner(page)
    assert result.detected is True
    assert result.dismissed is True
    assert result.method == "vendor_css"


@pytest.mark.asyncio
async def test_text_match_english():
    """English 'Accept all' text matched."""
    page = _make_page(
        page_text="we use cookies to improve your experience",
        button_texts=["Accept all"],
    )
    result = await dismiss_cookie_banner(page)
    assert result.detected is True
    assert result.dismissed is True
    assert result.method == "text_match"


@pytest.mark.asyncio
async def test_text_match_german():
    """German 'Akzeptieren' text matched."""
    page = _make_page(
        page_text="wir verwenden cookies für die datenschutz",
        button_texts=["Akzeptieren"],
    )
    result = await dismiss_cookie_banner(page)
    assert result.detected is True
    assert result.dismissed is True
    assert result.method == "text_match"


@pytest.mark.asyncio
async def test_text_match_french():
    """French 'Accepter tout' text matched."""
    page = _make_page(
        page_text="nous utilisons des cookies",
        button_texts=["Accepter tout"],
    )
    result = await dismiss_cookie_banner(page)
    assert result.detected is True
    assert result.dismissed is True
    assert result.method == "text_match"


@pytest.mark.asyncio
async def test_text_match_spanish():
    """Spanish 'Aceptar todo' text matched."""
    page = _make_page(
        page_text="utilizamos cookies para la privacidad",
        button_texts=["Aceptar todo"],
    )
    result = await dismiss_cookie_banner(page)
    assert result.detected is True
    assert result.dismissed is True
    assert result.method == "text_match"


@pytest.mark.asyncio
async def test_text_match_italian():
    """Italian 'Accetta tutto' text matched."""
    page = _make_page(
        page_text="utilizziamo i cookie per la privacy",
        button_texts=["Accetta tutto"],
    )
    result = await dismiss_cookie_banner(page)
    assert result.detected is True
    assert result.dismissed is True
    assert result.method == "text_match"


@pytest.mark.asyncio
async def test_no_banner_returns_not_detected():
    """No banner on page returns detected=False."""
    page = _make_page(page_text="just a normal page with no cookie info")
    result = await dismiss_cookie_banner(page)
    assert result.detected is False
    assert result.dismissed is False
    assert result.method == "none"


@pytest.mark.asyncio
async def test_result_dataclass():
    """CookieBannerResult defaults are correct."""
    result = CookieBannerResult()
    assert result.detected is False
    assert result.dismissed is False
    assert result.method == "none"


@pytest.mark.asyncio
async def test_vendor_selectors_coverage():
    """Vendor selectors list has expected coverage."""
    assert len(VENDOR_SELECTORS) >= 20
    assert "#onetrust-accept-btn-handler" in VENDOR_SELECTORS
    assert "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll" in VENDOR_SELECTORS
    assert ".truste-consent-button" in VENDOR_SELECTORS


@pytest.mark.asyncio
async def test_text_patterns_multilingual():
    """Text patterns cover multiple languages."""
    patterns_lower = [p.lower() for p in ACCEPT_TEXT_PATTERNS]
    assert "accept all" in patterns_lower
    assert "akzeptieren" in patterns_lower
    assert "accepter" in patterns_lower
    assert "aceptar" in patterns_lower
    assert "accetta" in patterns_lower


@pytest.mark.asyncio
async def test_context_keywords_present():
    """Context keywords include cookie/privacy/gdpr."""
    assert "cookie" in COOKIE_CONTEXT_KEYWORDS
    assert "gdpr" in COOKIE_CONTEXT_KEYWORDS
    assert "privacy" in COOKIE_CONTEXT_KEYWORDS
