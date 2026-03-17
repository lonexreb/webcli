"""Cookie banner detection and auto-dismissal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

# Strategy 1: Vendor-specific CSS selectors (most specific, try first)
VENDOR_SELECTORS: list[str] = [
    # OneTrust
    "#onetrust-accept-btn-handler",
    "#onetrust-banner-sdk .onetrust-close-btn-handler",
    # Cookiebot
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#CybotCookiebotDialogBodyButtonAccept",
    "#CybotCookiebotDialogBodyLevelButtonAccept",
    # TrustArc
    ".truste-consent-button",
    ".truste_popframe .pdynamicbutton .call",
    # Quantcast
    ".qc-cmp2-summary-buttons button[mode='primary']",
    "#qcCmpButtons button.css-47sehv",
    # Didomi
    "#didomi-notice-agree-button",
    ".didomi-continue-without-agreeing",
    # Cookie Notice (WordPress)
    "#cookie-notice .cn-set-cookie",
    "#cookie-notice .cn-accept-cookie",
    # GDPR Cookie Compliance
    "#moove_gdpr_cookie_info_bar .mgbutton",
    "#moove_gdpr_cookie_info_bar .change-settings-button",
    # Osano
    ".osano-cm-accept-all",
    ".osano-cm-dialog--type_consent .osano-cm-accept",
    # Complianz
    ".cmplz-accept",
    "#cmplz-cookiebanner-container .cmplz-btn.cmplz-accept",
    # Cookie Consent (Insites)
    ".cc-btn.cc-allow",
    ".cc-banner .cc-btn.cc-dismiss",
    # Usercentrics
    "#uc-btn-accept-banner",
    "[data-testid='uc-accept-all-button']",
    # iubenda
    ".iubenda-cs-accept-btn",
    # LiveRamp / CMP
    "#consentAccept",
    # Generic patterns from common CMP implementations
    ".cookie-consent-accept",
    ".cookie-accept-all",
    ".js-cookie-accept",
    "[data-cookie-accept]",
    "[data-action='accept-cookies']",
]

# Strategy 2: Multilingual text patterns for accept buttons
ACCEPT_TEXT_PATTERNS: list[str] = [
    # English
    "Accept all",
    "Accept cookies",
    "Accept all cookies",
    "I agree",
    "I accept",
    "Allow all",
    "Allow cookies",
    "OK",
    "Got it",
    "Agree",
    # German
    "Akzeptieren",
    "Alle akzeptieren",
    "Alle Cookies akzeptieren",
    "Einverstanden",
    # French
    "Accepter",
    "Accepter tout",
    "Tout accepter",
    "J'accepte",
    # Spanish
    "Aceptar",
    "Aceptar todo",
    "Aceptar todas",
    # Italian
    "Accetta",
    "Accetta tutto",
    "Accetto",
    # Portuguese
    "Aceitar",
    "Aceitar tudo",
    # Dutch
    "Accepteren",
    "Alles accepteren",
    # Polish
    "Akceptuj",
    # Swedish
    "Acceptera",
    # Japanese
    "同意する",
    # Korean
    "동의",
]

# Context keywords that must be near the button to avoid false positives
COOKIE_CONTEXT_KEYWORDS: list[str] = [
    "cookie",
    "cookies",
    "gdpr",
    "privacy",
    "consent",
    "tracking",
    "datenschutz",
    "rgpd",
    "privacidad",
]


@dataclass
class CookieBannerResult:
    """Result of cookie banner detection and dismissal."""

    detected: bool = False
    dismissed: bool = False
    method: str = "none"  # "vendor_css" | "text_match" | "a11y" | "none"


async def dismiss_cookie_banner(page: Page) -> CookieBannerResult:
    """Detect and dismiss cookie consent banners.

    Tries three strategies in order of specificity:
    1. Vendor CSS selectors (most reliable)
    2. Multilingual text matching on buttons
    3. A11y role matching

    Returns:
        CookieBannerResult with detection and dismissal status.
    """
    # Strategy 1: Vendor CSS selectors
    result = await _try_vendor_selectors(page)
    if result.dismissed:
        return result

    # Strategy 2: Text matching with context check
    result = await _try_text_matching(page)
    if result.dismissed:
        return result

    # Strategy 3: A11y role matching
    result = await _try_a11y_matching(page)
    if result.dismissed:
        return result

    return CookieBannerResult(detected=False, dismissed=False, method="none")


async def _try_vendor_selectors(page: Page) -> CookieBannerResult:
    """Try clicking vendor-specific cookie banner selectors."""
    for selector in VENDOR_SELECTORS:
        try:
            element = await page.query_selector(selector)
            if element and await element.is_visible():
                await element.click(timeout=2000)
                await page.wait_for_timeout(500)
                return CookieBannerResult(detected=True, dismissed=True, method="vendor_css")
        except Exception:
            continue
    return CookieBannerResult()


async def _try_text_matching(page: Page) -> CookieBannerResult:
    """Try matching accept button text with context validation."""
    # First check if there's cookie/privacy context on the page
    try:
        page_text = await page.evaluate("() => document.body?.innerText?.toLowerCase() || ''")
        has_context = any(kw in page_text for kw in COOKIE_CONTEXT_KEYWORDS)
        if not has_context:
            return CookieBannerResult()
    except Exception:
        return CookieBannerResult()

    for pattern in ACCEPT_TEXT_PATTERNS:
        try:
            # Look for buttons/links with matching text
            for tag in ["button", "a", "[role='button']"]:
                elements = await page.query_selector_all(tag)
                for el in elements:
                    try:
                        text = await el.text_content()
                        if text and text.strip().lower() == pattern.lower():
                            if await el.is_visible():
                                await el.click(timeout=2000)
                                await page.wait_for_timeout(500)
                                return CookieBannerResult(
                                    detected=True, dismissed=True, method="text_match"
                                )
                    except Exception:
                        continue
        except Exception:
            continue
    return CookieBannerResult(detected=True, dismissed=False, method="none")


async def _try_a11y_matching(page: Page) -> CookieBannerResult:
    """Try matching via accessibility tree button names."""
    try:
        snapshot = await page.accessibility.snapshot()
        if not snapshot:
            return CookieBannerResult()

        accept_names = {p.lower() for p in ACCEPT_TEXT_PATTERNS}

        def _find_accept_button(node: dict) -> str | None:
            role = node.get("role", "")
            name = (node.get("name") or "").strip()
            if role == "button" and name.lower() in accept_names:
                return name
            for child in node.get("children", []):
                found = _find_accept_button(child)
                if found:
                    return found
            return None

        button_name = _find_accept_button(snapshot)
        if button_name:
            # Click using the accessible name
            await page.get_by_role("button", name=button_name).click(timeout=2000)
            await page.wait_for_timeout(500)
            return CookieBannerResult(detected=True, dismissed=True, method="a11y")
    except Exception:
        pass
    return CookieBannerResult()
