import pytest
import sys
sys.path.insert(0, "scripts")
from competitive_analyzer import fetch_competitor_data, compare_competitors
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_requests():
    """Mock all external HTTP requests for testing."""
    with patch("competitive_analyzer.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head><title>Test Site</title>
        <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Main Heading</h1>
            <h2>Sub Heading</h2>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. </p>
            <a href="/internal-link">Internal</a>
            <a href="https://external.com">External</a>
            <img src="test.jpg" alt="Test image">
            <script type="application/ld+json">{"@type":"WebPage"}</script>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        yield mock_get


def test_fetch_competitor_data_returns_structure():
    """Test with a known domain that won't be blocked."""
    result = fetch_competitor_data("example.com")
    assert "domain" in result
    assert "word_count" in result or "error" in result


def test_compare_competitors_returns_structure():
    result = compare_competitors("example.com", ["example.org"])
    assert "target_domain" in result
    assert "share_of_voice" in result
    assert "competitive_gaps" in result
    assert result["target_domain"] == "example.com"
    assert "example.org" in result["competitors"]


def test_share_of_voice_keys():
    result = compare_competitors("example.com", ["example.org"])
    assert "example.com" in result["share_of_voice"]
    assert "example.org" in result["share_of_voice"]


def test_competitive_gaps_structure():
    result = compare_competitors("example.com", ["example.org"])
    assert "example.org" in result["competitive_gaps"]
    for metric, gap_data in result["competitive_gaps"]["example.org"].items():
        assert "target" in gap_data
        assert "competitor" in gap_data
        assert "gap" in gap_data
        assert "gap_pct" in gap_data