import pytest
import sys
sys.path.insert(0, "scripts")
from multimodal_analyzer import (
    analyze_images, analyze_video_content, analyze_multimodal,
    analyze_charts_and_infographics, analyze_audio_content
)
from bs4 import BeautifulSoup


def test_analyze_images_all_have_alt():
    html = """
    <html><body>
        <img src="a.jpg" alt="Product feature overview" />
        <img src="b.jpg" alt="Team photo 2024" />
        <img src="c.jpg" alt="Chart showing growth" />
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_images(soup)
    assert result["total_images"] == 3
    assert result["images_with_alt"] == 3
    assert result["alt_coverage_pct"] == 100.0


def test_analyze_images_missing_alt():
    html = "<html><body><img src='a.jpg' alt='Good alt' /><img src='b.jpg' /></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_images(soup)
    assert result["images_missing_alt"] == 1
    assert result["alt_coverage_pct"] == 50.0


def test_analyze_multimodal_composite():
    html = """
    <html><body>
        <img src="a.jpg" alt="Descriptive text here" />
        <img src="b.jpg" alt="Another descriptive" />
        <figure><figcaption>Chart 1 description</figcaption></figure>
    </body></html>
    """
    result = analyze_multimodal(html)
    assert "multimodal_composite_score" in result
    assert 0 <= result["multimodal_composite_score"] <= 100
    assert isinstance(result["recommendations"], list)


def test_analyze_video_youtube():
    html = """
    <html><body>
        <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_video_content(soup)
    assert len(result["youtube_videos"]) == 1
    assert result["youtube_videos"][0]["video_id"] == "dQw4w9WgXcQ"


def test_analyze_charts_with_figcaption():
    html = """
    <html><body>
        <figure><figcaption>Sales growth chart</figcaption></figure>
        <svg aria-label="Trend graph"></svg>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_charts_and_infographics(soup)
    assert result["figures_with_captions"] == 1
    assert result["svgs_with_accessibility_labels"] == 1
    assert result["chart_accessibility_score"] > 0
