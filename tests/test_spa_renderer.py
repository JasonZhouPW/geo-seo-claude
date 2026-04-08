import pytest
import sys
sys.path.insert(0, "scripts")
from spa_renderer import is_playwright_available, render_spa_page, enhance_fetch_result


def test_is_playwright_available_returns_bool():
    result = is_playwright_available()
    assert isinstance(result, bool)


def test_render_spa_page_without_playwright():
    """When Playwright is not installed, should return error dict with fallback_used=True."""
    # Temporarily check if playwright is available
    if is_playwright_available():
        pytest.skip("Playwright is installed, cannot test fallback path")

    result = render_spa_page("https://example.com")
    assert "error" in result
    assert result["fallback_used"] is True


def test_render_spa_page_with_playwright_installed():
    """When Playwright IS installed, test with a simple page."""
    if not is_playwright_available():
        pytest.skip("Playwright not installed")

    result = render_spa_page("https://example.com", wait_time=1000)
    assert "error" not in result
    assert result["fallback_used"] is False
    assert "rendered_text_length" in result
    assert "title" in result


def test_enhance_fetch_result_no_spa():
    """When page already has SSR content, should not use Playwright."""
    fetch_result = {"url": "https://example.com", "has_ssr_content": True}
    result = enhance_fetch_result(fetch_result, use_playwright_fallback=True)
    assert result["final_content_source"] == "requests"
    assert "spa_rendering" not in result


def test_enhance_fetch_result_with_spa_fallback():
    """When page lacks SSR content and Playwright is available, should use Playwright."""
    if not is_playwright_available():
        pytest.skip("Playwright not installed")

    fetch_result = {"url": "https://example.com", "has_ssr_content": False}
    result = enhance_fetch_result(fetch_result, use_playwright_fallback=True)
    assert result["final_content_source"] == "playwright"
    assert "spa_rendering" in result