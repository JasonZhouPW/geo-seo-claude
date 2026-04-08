import pytest
import sys
sys.path.insert(0, "scripts")
from claude_platform_analyzer import analyze_claude_readiness
from bs4 import BeautifulSoup


def test_claude_readiness_high_score():
    html = """
    <html><body>
        <h1>SEO Best Practices 2026</h1>
        <h2>Why Technical SEO Matters</h2>
        <h2>Site Speed Optimization</h2>
        <h2>Mobile First Indexing</h2>
        <time datetime="2026-01-15">January 15, 2026</time>
        <p>This comprehensive guide provides 15 years of hands-on experience in technical SEO optimization. Dr. Jane Smith, a certified search expert with 15+ years of experience in the search industry, explains the key factors that drive better rankings. The data shows 60% improvement in search visibility when proper technical foundations are implemented. This paragraph has well over 50 words and demonstrates expertise level content that AI systems can extract and cite effectively for authoritative sources.</p>
        <ul><li>Site speed optimization</li><li>Mobile-first indexing</li><li>Core Web Vitals</li></ul>
        <blockquote>Technical SEO is the foundation of all search visibility.</blockquote>
        <ol class="references">
            <li><a href="https://example.com/ref1">Research on SEO</a></li>
            <li><a href="https://example.com/ref2">Industry Study</a></li>
            <li><a href="https://example.com/ref3">Industry Report</a></li>
            <li><a href="https://example.com/ref4">Expert Guide</a></li>
        </ol>
    </body></html>
    """
    result = analyze_claude_readiness(html)
    assert result["claude_readiness_score"] > 50
    assert result["authority_signals"]["authority_score"] > 0


def test_claude_readiness_low_score():
    html = "<html><body><p>Short text.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert result["claude_readiness_score"] < 50


def test_claude_readiness_returns_structure():
    html = "<html><body><p>Some content here with multiple words to make it meaningful passage.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert "claude_readiness_score" in result
    assert "passage_analysis" in result
    assert "authority_signals" in result
    assert "structure_score" in result
    assert "citation_compatibility" in result
    assert "recommendations" in result


def test_paragraph_length_analysis():
    html = """
    <html><body>
        <p>This is a short paragraph.</p>
        <p>This is a much longer paragraph with many more words that should be considered a better quality passage for AI citation systems. It has well over fifty words which is the threshold needed for a good passage. The content discusses important topics and provides substantive value. This paragraph should be recognized as a quality passage for AI citation because it contains enough words and meaningful content.</p>
    </body></html>
    """
    result = analyze_claude_readiness(html)
    assert result["passage_analysis"]["total_paragraphs"] == 2
    assert result["passage_analysis"]["good_passages"] >= 1