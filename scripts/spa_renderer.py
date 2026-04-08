#!/usr/bin/env python3
"""
SPA Renderer — Uses Playwright to render JavaScript-heavy pages.
"""

import sys
import json
from typing import Dict


def is_playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


def render_spa_page(url: str, wait_time: int = 3000) -> Dict:
    """Render a JavaScript-heavy SPA page using Playwright."""
    if not is_playwright_available():
        return {
            "error": "Playwright not installed. Run: pip install playwright && playwright install chromium",
            "fallback_used": True,
        }

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            response = page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(wait_time)

            rendered_html = page.content()
            rendered_text = page.inner_text("body")
            title = page.title()

            has_dynamic_content = len(rendered_text) > 500

            browser.close()

            return {
                "url": url,
                "status": response.status if response else None,
                "title": title,
                "rendered_text_length": len(rendered_text),
                "rendered_html_length": len(rendered_html),
                "has_dynamic_content": has_dynamic_content,
                "rendering_method": "CSR" if len(rendered_text) > 500 else "SSR",
                "text_content": rendered_text[:5000],
                "fallback_used": False,
            }
        except Exception as e:
            browser.close()
            return {"error": str(e), "fallback_used": False}


def enhance_fetch_result(fetch_result: Dict, use_playwright_fallback: bool = True) -> Dict:
    """Enhance a fetch_page result with Playwright rendering for SPA detection."""
    if not fetch_result.get("has_ssr_content") and use_playwright_fallback:
        if is_playwright_available():
            spa_result = render_spa_page(fetch_result["url"])
            if "error" not in spa_result:
                return {
                    **fetch_result,
                    "spa_rendering": spa_result,
                    "final_content_source": "playwright",
                }
    return {**fetch_result, "final_content_source": "requests"}


if __name__ == "__main__":
    import json
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    result = render_spa_page(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))