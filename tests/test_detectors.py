"""Tests for auth and CAPTCHA page detection."""

from __future__ import annotations

from unittest.mock import AsyncMock, PropertyMock

import pytest

from site2cli.browser.detectors import AuthDetectionResult, detect_auth_page


def _make_page(
    url: str = "https://example.com",
    signals: dict | None = None,
):
    """Create a mock page for auth detection."""
    page = AsyncMock()
    type(page).url = PropertyMock(return_value=url)

    default_signals = {
        "hasPasswordField": False,
        "hasLoginHeading": False,
        "hasCaptchaIframe": False,
        "hasMfaKeyword": False,
        "headingTexts": [],
        "bodyText": "",
    }
    if signals:
        default_signals.update(signals)

    page.evaluate = AsyncMock(return_value=default_signals)
    return page


@pytest.mark.asyncio
async def test_google_sso_url():
    page = _make_page(url="https://accounts.google.com/signin/v2")
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "sso"
    assert result.provider == "google"
    assert result.requires_human is True


@pytest.mark.asyncio
async def test_microsoft_sso_url():
    page = _make_page(url="https://login.microsoftonline.com/common/oauth2")
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "sso"
    assert result.provider == "microsoft"


@pytest.mark.asyncio
async def test_auth0_url():
    page = _make_page(url="https://myapp.auth0.com/login")
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "sso"
    assert result.provider == "auth0"


@pytest.mark.asyncio
async def test_generic_login_url():
    page = _make_page(url="https://example.com/login")
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "login"


@pytest.mark.asyncio
async def test_normal_page_not_detected():
    page = _make_page(url="https://example.com/dashboard")
    result = await detect_auth_page(page)
    assert result.detected is False


@pytest.mark.asyncio
async def test_password_field_with_login_heading():
    page = _make_page(
        url="https://example.com/account",
        signals={
            "hasPasswordField": True,
            "headingTexts": ["sign in to your account"],
            "bodyText": "sign in to your account email password",
        },
    )
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "login"
    assert result.requires_human is True


@pytest.mark.asyncio
async def test_captcha_detection():
    page = _make_page(
        url="https://example.com/verify",
        signals={"hasCaptchaIframe": True},
    )
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "captcha"
    assert result.requires_human is True


@pytest.mark.asyncio
async def test_mfa_detection():
    page = _make_page(
        url="https://example.com/verify",
        signals={"bodyText": "enter your two-factor authentication code"},
    )
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "mfa"
    assert result.requires_human is True


@pytest.mark.asyncio
async def test_result_defaults():
    result = AuthDetectionResult()
    assert result.detected is False
    assert result.kind == "unknown"
    assert result.provider is None
    assert result.requires_human is False


@pytest.mark.asyncio
async def test_password_field_alone():
    """Password field alone triggers login detection."""
    page = _make_page(
        url="https://example.com/settings",
        signals={"hasPasswordField": True, "headingTexts": []},
    )
    result = await detect_auth_page(page)
    assert result.detected is True
    assert result.kind == "login"
