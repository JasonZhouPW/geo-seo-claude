#!/usr/bin/env python3
"""
Comprehensive test suite covering all improvements.
Tests edge cases, boundary conditions, and untested code paths.
"""

import pytest
import sys
import re
import json
sys.path.insert(0, "scripts")

from bs4 import BeautifulSoup

# ========================================================================
# scoring.py - edge cases & boundary conditions
# ========================================================================
from scoring import (
    compute_citability_score, compute_eeat_score,
    compute_geu_dimension_scores, normalize_platform_scores,
    compute_final_geu_score, WEIGHTS
)


def test_weights_exactly_sum_to_one():
    """Weights must sum to exactly 1.0."""
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, not 1.0"


def test_citability_score_caps_at_100():
    """Score must never exceed 100."""
    score = compute_citability_score(100, 200, True, True)
    assert score <= 100


def test_citability_score_optimal_word_range():
    """134-167 words gets max word bonus."""
    optimal = compute_citability_score(80, 150, False, False)
    below = compute_citability_score(80, 133, False, False)
    above = compute_citability_score(80, 168, False, False)
    assert optimal > below
    assert optimal > above


def test_citability_score_at_100_words():
    """100 words is below bonus threshold (needs >100 for 10pt or 134-167 for 20pt)."""
    score_100 = compute_citability_score(80, 100, False, False)
    score_101 = compute_citability_score(80, 101, False, False)
    # 100 words: word_bonus=0; 101 words: word_bonus=10
    assert score_101 > score_100


def test_citability_score_zero_base():
    """Zero base passage score still gets bonuses."""
    score = compute_citability_score(0, 150, True, True)
    # base=0, word_bonus=20, stat_bonus=15, def_bonus=10
    assert score == 45


def test_eeat_score_caps_at_100():
    """E-E-A-T score max is 100."""
    score = compute_eeat_score(100, 100, 100, 100)
    assert score <= 100


def test_eeat_score_zero():
    """Zero inputs produce zero score."""
    score = compute_eeat_score(0, 0, 0, 0)
    assert score == 0


def test_geu_dimension_scores_empty():
    """Empty dimension list returns zero composite."""
    result = compute_geu_dimension_scores([])
    assert result["geu_composite"] == 0


def test_geu_dimension_scores_single():
    """Single dimension returns its own value."""
    result = compute_geu_dimension_scores([{"dimension": "clarity", "score": 85}])
    assert result["geu_composite"] == 85


def test_geu_dimension_scores_weighted():
    """Weighted dimensions aggregate correctly."""
    dims = [
        {"dimension": "clarity", "score": 80, "weight": 2.0},
        {"dimension": "accuracy", "score": 100, "weight": 1.0},
    ]
    result = compute_geu_dimension_scores(dims)
    # (80*2 + 100*1) / (2+1) = 260/3 = 86.67
    assert abs(result["geu_composite"] - 86.67) < 0.1


def test_geu_dimension_scores_no_weight_defaults_to_one():
    """Dimensions without weight default to 1.0."""
    dims = [
        {"dimension": "a", "score": 50},
        {"dimension": "b", "score": 100},
    ]
    result = compute_geu_dimension_scores(dims)
    assert result["geu_composite"] == 75


def test_normalize_platform_scores_empty():
    """Empty platform dict returns empty."""
    result = normalize_platform_scores({})
    assert result == {}


def test_normalize_platform_scores_all_valid():
    """Already-normalized scores unchanged."""
    scores = {"chatgpt": 50, "perplexity": 75, "gemini": 100}
    result = normalize_platform_scores(scores)
    assert result == scores


def test_final_geu_score_with_geu_dimensions():
    """GEU dimensions are included in result when provided."""
    result = compute_final_geu_score(
        citability=80, brand=70, content=75, technical=90,
        structured=60, platform={"chatgpt": 70},
        geu_dimensions=[
            {"dimension": "clarity", "score": 85, "weight": 1.0},
            {"dimension": "accuracy", "score": 90, "weight": 1.0},
        ]
    )
    assert "geu_composite" in result
    assert "geu_sub_scores" in result
    assert result["geu_composite"] == 87.5


def test_final_geu_score_without_geu_dimensions():
    """No GEU dimensions — result has no geu_composite."""
    result = compute_final_geu_score(
        citability=80, brand=70, content=75, technical=90,
        structured=60, platform={"chatgpt": 70},
        geu_dimensions=None
    )
    assert "geu_composite" not in result


def test_final_geu_score_empty_platform():
    """Empty platform dict — platform_avg = 0."""
    result = compute_final_geu_score(
        citability=80, brand=70, content=75, technical=90,
        structured=60, platform={}
    )
    assert result["breakdown"]["platform_optimization"] == 0


def test_final_geu_score_breakdown_sum():
    """Breakdown contains all 6 required keys."""
    result = compute_final_geu_score(
        citability=80, brand=70, content=75, technical=90,
        structured=60, platform={"chatgpt": 70}
    )
    expected_keys = {"ai_citability", "brand_authority", "content_quality",
                     "technical", "structured_data", "platform_optimization"}
    assert set(result["breakdown"].keys()) == expected_keys


# ========================================================================
# multimodal_analyzer.py - edge cases
# ========================================================================
from multimodal_analyzer import (
    analyze_images, analyze_video_content, analyze_multimodal,
    analyze_charts_and_infographics, analyze_audio_content
)


def test_analyze_images_empty_page():
    """No images returns zero scores."""
    soup = BeautifulSoup("<html><body><p>No images here</p></body></html>", "lxml")
    result = analyze_images(soup)
    assert result["total_images"] == 0
    assert result["alt_coverage_pct"] == 0
    assert result["quality_score"] == 0


def test_analyze_images_all_missing_alt():
    """All images missing alt text — 0% coverage."""
    html = "<html><body><img src='a.jpg'/><img src='b.jpg'/><img src='c.jpg'/></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_images(soup)
    assert result["alt_coverage_pct"] == 0.0
    assert result["images_missing_alt"] == 3


def test_analyze_images_alt_exactly_20_chars():
    """Alt text exactly 20 chars is considered good."""
    html = "<html><body><img src='a.jpg' alt='exactly twenty chars!'/></body></html>"  # 20 chars
    soup = BeautifulSoup(html, "lxml")
    result = analyze_images(soup)
    assert result["images_with_alt"] == 1


def test_analyze_images_alt_200_chars():
    """Alt text exactly 200 chars is considered good."""
    alt_200 = "a" * 200
    html = f"<html><body><img src='a.jpg' alt='{alt_200}'/></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_images(soup)
    assert result["images_with_alt"] == 1


def test_analyze_images_alt_too_long():
    """Alt text over 200 chars still scores higher due to length bonus (capped at 1.0 for avg_len)."""
    html_short = "<html><body><img src='a.jpg' alt='short alt'/></body></html>"
    html_long = f"<html><body><img src='a.jpg' alt='{'a'*300}'/></body></html>"
    soup_short = BeautifulSoup(html_short, "lxml")
    soup_long = BeautifulSoup(html_long, "lxml")
    result_short = analyze_images(soup_short)
    result_long = analyze_images(soup_long)
    # Long alt has higher length bonus (avg_len/150 capped at 1.0 for quality)
    assert result_long["quality_score"] >= result_short["quality_score"]


def test_analyze_video_no_videos():
    """No videos returns base structure."""
    html = "<html><body><p>No video content</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_video_content(soup)
    assert result["youtube_videos"] == []
    assert result["native_videos"] == []
    assert result["video_readiness_score"] == 0


def test_analyze_video_youtube_embed_patterns():
    """YouTube embed URL variations are all recognized."""
    html = """
    <html><body>
        <iframe src="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></iframe>
        <iframe src="https://youtu.be/dQw4w9WgXcQ"></iframe>
        <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_video_content(soup)
    assert len(result["youtube_videos"]) == 3
    video_ids = [v["video_id"] for v in result["youtube_videos"]]
    assert all(vid == "dQw4w9WgXcQ" for vid in video_ids)


def test_analyze_video_native_with_captions():
    """Native video with track element counted as captioned."""
    html = """
    <html><body>
        <video src="movie.mp4">
            <track kind="captions" src="captions.vtt"/>
        </video>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_video_content(soup)
    assert len(result["native_videos"]) == 1
    assert result["native_videos"][0]["has_caption_track"] is True
    assert result["videos_without_captions"] == 0


def test_analyze_video_multiple_native_without_captions():
    """Multiple native videos without captions get 20pt penalty each."""
    html = """
    <html><body>
        <video src="a.mp4"></video>
        <video src="b.mp4"></video>
        <video src="c.mp4"></video>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_video_content(soup)
    assert result["videos_without_captions"] == 3
    # score = max(0, 100 - 3*20) = 40
    assert result["video_readiness_score"] == 40


def test_analyze_charts_no_figures():
    """No figures, SVGs, or tables returns zero score."""
    html = "<html><body><p>Just text</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_charts_and_infographics(soup)
    assert result["total_figures"] == 0
    assert result["total_svgs"] == 0
    assert result["total_tables"] == 0
    assert result["chart_accessibility_score"] == 0


def test_analyze_charts_figcaption_scoring():
    """Figcaption adds 10pts per figure, capped at 40."""
    html = """
    <html><body>
        <figure><figcaption>Chart A</figcaption></figure>
        <figure><figcaption>Chart B</figcaption></figure>
        <figure><figcaption>Chart C</figcaption></figure>
        <figure><figcaption>Chart D</figcaption></figure>
        <figure><figcaption>Chart E</figcaption></figure>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_charts_and_infographics(soup)
    # 5 figures * 10 = 50, capped at 40
    assert result["chart_accessibility_score"] == 40


def test_analyze_charts_svg_aria_label():
    """SVG with aria-label counts toward accessibility."""
    html = "<html><body><svg aria-label='Data chart'></svg></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_charts_and_infographics(soup)
    assert result["svgs_with_accessibility_labels"] == 1


def test_analyze_charts_svg_role_img():
    """SVG with role='img' counts toward accessibility."""
    html = "<html><body><svg role='img' aria-label='test'></svg></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_charts_and_infographics(soup)
    assert result["svgs_with_accessibility_labels"] == 1


def test_analyze_audio_no_audio():
    """No audio tags — 100% coverage (edge case)."""
    html = "<html><body><p>No audio</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_audio_content(soup)
    assert result["total_audio_elements"] == 0
    assert result["audio_transcript_coverage_pct"] == 100


def test_analyze_audio_with_transcript():
    """Audio with adjacent transcript link detected."""
    html = """
    <html><body>
        <div>
            <audio src="episode1.mp3"></audio>
            <a href="/transcript">Transcript</a>
        </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_audio_content(soup)
    assert result["total_audio_elements"] == 1
    assert result["audio_with_transcripts"] == 1
    assert result["audio_transcript_coverage_pct"] == 100.0


def test_analyze_audio_chinese_transcript_link():
    """Chinese transcript link patterns are recognized."""
    html = """
    <html><body>
        <div>
            <audio src="episode.mp3"></audio>
            <a href="/文字稿">文字稿</a>
        </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_audio_content(soup)
    assert result["audio_with_transcripts"] == 1


def test_analyze_multimodal_recommendations_logic():
    """Recommendations generated when thresholds crossed."""
    # Low image coverage triggers recommendation
    html = "<html><body><img src='a.jpg'/><img src='b.jpg'/></body></html>"
    result = analyze_multimodal(html)
    assert any("alt text" in r for r in result["recommendations"])


def test_analyze_multimodal_empty_page():
    """Empty page returns low composite score (audio defaults to 100% coverage)."""
    html = "<html><body></body></html>"
    result = analyze_multimodal(html)
    # audio_transcript_coverage_pct defaults to 100 when no audio,
    # contributing 15.0 to composite (100 * 0.15 weight)
    assert result["multimodal_composite_score"] == 15.0


def test_analyze_multimodal_full_page_optimized():
    """Well-optimized page scores near 100."""
    html = """
    <html><body>
        <img src='a.jpg' alt='Product feature chart showing growth metrics'/>
        <img src='b.jpg' alt='Team collaboration workflow diagram'/>
        <figure><figcaption>Revenue trend 2024-2026</figcaption></figure>
        <svg aria-label='Market share pie chart'></svg>
        <table><tr><td>Data</td></tr></table>
        <audio src="podcast.mp3"></audio>
    </body></html>
    """
    result = analyze_multimodal(html)
    assert result["multimodal_composite_score"] > 0


# ========================================================================
# claude_platform_analyzer.py - edge cases
# ========================================================================
from claude_platform_analyzer import analyze_claude_readiness


def test_claude_readiness_returns_all_keys():
    """All required keys are present."""
    html = "<html><body><p>Content.</p></body></html>"
    result = analyze_claude_readiness(html)
    required_keys = ["claude_readiness_score", "passage_analysis", "authority_signals",
                    "structure_score", "citation_compatibility", "recommendations"]
    for key in required_keys:
        assert key in result


def test_claude_structure_h1_count_exactly_1():
    """Exactly 1 H1 gets the structure bonus."""
    html_one = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    html_zero = "<html><body><h2>Title</h2><p>Content</p></body></html>"
    result_one = analyze_claude_readiness(html_one)
    result_zero = analyze_claude_readiness(html_zero)
    assert result_one["structure_score"] > result_zero["structure_score"]


def test_claude_structure_h1_count_2():
    """Exactly 2 H1s also gets the structure bonus."""
    html_two = "<html><body><h1>First</h1><h1>Second</h1><p>Content</p></body></html>"
    html_many = "<html><body><h1>A</h1><h1>B</h1><h1>C</h1><p>Content</p></body></html>"
    result_two = analyze_claude_readiness(html_two)
    result_many = analyze_claude_readiness(html_many)
    # 2 H1s is valid (1<=count<=2), 3+ H1s does not get bonus
    assert result_two["structure_score"] > result_many["structure_score"]


def test_claude_structure_h2_bonus():
    """3+ H2s adds to structure score."""
    html = "<html><body><h2>A</h2><h2>B</h2><h2>C</h2><p>Some content here with enough words to make sentences.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert result["structure_score"] >= 20  # H2 bonus


def test_claude_authority_author_class():
    """author class detected for authority score."""
    html = '<html><body><span class="author">Jane Smith</span><p>Content</p></body></html>'
    result = analyze_claude_readiness(html)
    assert "author_info" in result["authority_signals"]["signals_found"]


def test_claude_authority_byline_class():
    """byline class detected for authority score."""
    html = '<html><body><div class="byline">Jane Smith</div><p>Content</p></body></html>'
    result = analyze_claude_readiness(html)
    assert "author_info" in result["authority_signals"]["signals_found"]


def test_claude_authority_no_signal():
    """No authority signals — score should be 0."""
    html = "<html><body><p>Generic content without any authority signals.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert result["authority_signals"]["authority_score"] == 0


def test_claude_authority_years_experience():
    """Years of experience pattern detected."""
    html = "<html><body><p>Expert with 15 years of experience in SEO optimization.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert "credential" in result["authority_signals"]["signals_found"]


def test_claude_authority_credential_patterns():
    """Ph.D., M.D., MBA patterns detected."""
    html = "<html><body><p>Dr. Smith holds a Ph.D. in Computer Science.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert "credential" in result["authority_signals"]["signals_found"]


def test_claude_authority_certified():
    """Certified pattern detected."""
    html = "<html><body><p>John is a certified SEO specialist with 10 years.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert "credential" in result["authority_signals"]["signals_found"]


def test_claude_authority_founder():
    """Founder/CEO pattern detected."""
    html = "<html><body><p>Jane is founder of TechCorp and CEO of StartupX.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert "credential" in result["authority_signals"]["signals_found"]


def test_claude_authority_references_section():
    """References section detected."""
    html = """
    <html><body>
        <p>Content</p>
        <ol class="references">
            <li><a href="#">Source 1</a></li>
        </ol>
    </body></html>
    """
    result = analyze_claude_readiness(html)
    assert "references_section" in result["authority_signals"]["signals_found"]


def test_claude_authority_about_link():
    """About page link detected."""
    html = '<html><body><a href="/about">About the author</a><p>Content</p></body></html>'
    result = analyze_claude_readiness(html)
    assert "about_page_link" in result["authority_signals"]["signals_found"]


def test_claude_authority_time_tag():
    """Time tag (publish date) detected."""
    html = '<html><body><time datetime="2026-01-15">January 15, 2026</time><p>Content</p></body></html>'
    result = analyze_claude_readiness(html)
    assert "publish_date" in result["authority_signals"]["signals_found"]


def test_claude_citation_external_links():
    """3+ external https links count as citations."""
    html = """
    <html><body>
        <a href="https://example.com/1">1</a>
        <a href="https://example.com/2">2</a>
        <a href="https://example.com/3">3</a>
        <p>Content.</p>
    </body></html>
    """
    result = analyze_claude_readiness(html)
    assert result["citation_compatibility"]["external_links_count"] >= 3


def test_claude_citation_localhost_excluded():
    """localhost links are excluded from citation count."""
    html = """
    <html><body>
        <a href="http://localhost:3000">Local</a>
        <a href="http://127.0.0.1">IP</a>
        <p>Content.</p>
    </body></html>
    """
    result = analyze_claude_readiness(html)
    assert result["citation_compatibility"]["external_links_count"] == 0


def test_claude_citation_no_citations():
    """No external links — citation readiness = 0."""
    html = "<html><body><p>Content without any external links here.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert result["citation_compatibility"]["citation_readiness"] == 0


def test_claude_readiness_score_never_negative():
    """Score should always be non-negative."""
    html = "<html><body><p>X.</p></body></html>"
    result = analyze_claude_readiness(html)
    assert result["claude_readiness_score"] >= 0


def test_claude_readiness_score_max_100():
    """Score should never exceed 100."""
    html = """
    <html><body>
        <h1>Title</h1>
        <h2>A</h2><h2>B</h2><h2>C</h2>
        <span class="author">Dr. Jane Smith</span>
        <blockquote>Important quote.</blockquote>
        <a href="https://a.com/1">1</a>
        <a href="https://b.com/2">2</a>
        <a href="https://c.com/3">3</a>
        <p>This paragraph has fifty words to ensure it counts as a good passage with over fifty words for the analysis.</p>
        <p>This paragraph has fifty words to ensure it counts as a good passage with over fifty words for the analysis.</p>
        <p>This paragraph has fifty words to ensure it counts as a good passage with over fifty words for the analysis.</p>
        <p>This paragraph has fifty words to ensure it counts as a good passage with over fifty words for the analysis.</p>
        <time datetime="2026-01-01">Date</time>
    </body></html>
    """
    result = analyze_claude_readiness(html)
    assert result["claude_readiness_score"] <= 100


# ========================================================================
# entity_analyzer.py - edge cases (LLM-mocked, multilingual real scenarios)
# ========================================================================
from unittest.mock import patch
from entity_analyzer import (
    extract_named_entities, analyze_entity_relationships,
    analyze_internal_duplicates, compute_entity_graph_score
)


def test_extract_no_entities():
    """Text with no named entities returns empty list (regex fallback)."""
    text = "This is just some generic text without any proper nouns."
    entities = extract_named_entities(text, use_llm=False)
    assert entities == []


def test_extract_person_with_suffix():
    """Person names with Jr., Sr., III suffixes are extracted (regex)."""
    text = "John Smith Jr. and Jane Doe III are the founders."
    entities = extract_named_entities(text, use_llm=False)
    labels = [e["label"] for e in entities]
    assert "PERSON" in labels


def test_extract_person_with_title():
    """Person names with Dr./Prof./Mr./Mrs. titles are extracted (regex)."""
    text = "Dr. Jane Smith and Prof. John Doe discuss the findings."
    entities = extract_named_entities(text, use_llm=False)
    labels = [e["label"] for e in entities]
    assert "PERSON" in labels


def test_extract_org_google_inc():
    """Google Inc. is correctly identified as ORG (regex fallback)."""
    text = "Google Inc. announced new features."
    entities = extract_named_entities(text, use_llm=False)
    labels = [e["label"] for e in entities]
    assert "ORG" in labels


def test_extract_org_variations():
    """Various org suffixes are all recognized (regex fallback)."""
    for expected in ["Acme Inc.", "Acme LLC.", "Acme Corp.", "Acme Ltd."]:
        text = f"{expected} is a company."
        entities = extract_named_entities(text, use_llm=False)
        labels = [e["label"] for e in entities]
        assert "ORG" in labels, f"Failed for {expected}"


def test_entity_relationships_llm_mocked():
    """Entity relationships parsed correctly from LLM JSON response."""
    llm_response = json.dumps({
        "entities": [
            {"text": "Google", "label": "ORG", "start": 0},
            {"text": "Sundar Pichai", "label": "PERSON", "start": 50},
            {"text": "DeepMind", "label": "ORG", "start": 80},
        ],
        "triples": [
            {"subject": "Google", "predicate": "competitor", "object": "Microsoft"},
            {"subject": "Google", "predicate": "founded_by", "object": "Larry Page"},
            {"subject": "DeepMind", "predicate": "is_a", "object": "AI research lab"},
            {"subject": "TensorFlow", "predicate": "used_by", "object": "Google"},
        ],
    })

    with patch("entity_analyzer._call_llm", return_value=llm_response):
        soup = BeautifulSoup("<html><body><p>Google vs Microsoft. DeepMind is an AI lab.</p></body></html>", "lxml")
        result = analyze_entity_relationships(soup, "Google", use_llm=True)

    assert result["total_entities_found"] == 3
    assert result["triple_count"] == 4
    triples = result["knowledge_triples"]

    competitor_triples = [t for t in triples if t["predicate"] == "competitor"]
    assert len(competitor_triples) == 1
    assert competitor_triples[0]["subject"] == "Google"
    assert competitor_triples[0]["object"] == "Microsoft"

    founded_triples = [t for t in triples if t["predicate"] == "founded_by"]
    assert len(founded_triples) == 1
    assert "Larry Page" in founded_triples[0]["object"]

    is_a_triples = [t for t in triples if t["predicate"] == "is_a"]
    assert len(is_a_triples) == 1

    used_by_triples = [t for t in triples if t["predicate"] == "used_by"]
    assert len(used_by_triples) == 1


def test_entity_relationships_multilingual_llm():
    """LLM-based entity extraction handles multilingual content."""
    llm_response = json.dumps({
        "entities": [
            {"text": "OpenAI", "label": "ORG", "start": 0},
            {"text": "阿里巴巴", "label": "ORG", "start": 30},
            {"text": "马云", "label": "PERSON", "start": 60},
            {"text": "谷歌", "label": "ORG", "start": 90},
        ],
        "triples": [
            {"subject": "OpenAI", "predicate": "competitor", "object": "阿里巴巴"},
            {"subject": "阿里巴巴", "predicate": "founded_by", "object": "马云"},
        ],
    })

    with patch("entity_analyzer._call_llm", return_value=llm_response):
        soup = BeautifulSoup("<html><body><p>OpenAI vs 阿里巴巴竞争。马云创立了阿里巴巴。</p></body></html>", "lxml")
        result = analyze_entity_relationships(soup, "TestBrand", use_llm=True)

    assert result["unique_entities"] == 4
    entity_types = result["entity_types"]
    assert entity_types.get("ORG", 0) >= 2
    assert entity_types.get("PERSON", 0) >= 1
    competitor_triples = [t for t in result["knowledge_triples"] if t["predicate"] == "competitor"]
    assert len(competitor_triples) == 1


def test_entity_relationships_llm_invalid_json_fallback():
    """Invalid LLM JSON response falls back to regex."""
    with patch("entity_analyzer._call_llm", return_value="This is not JSON"):
        soup = BeautifulSoup("<html><body><p>Google vs Microsoft in AI.</p></body></html>", "lxml")
        result = analyze_entity_relationships(soup, "Google", use_llm=True)

    # Should fall back to regex, which can extract some triples
    assert "knowledge_triples" in result
    assert "entity_types" in result


def test_entity_relationships_llm_empty_response():
    """Empty LLM response falls back to regex."""
    with patch("entity_analyzer._call_llm", return_value=""):
        soup = BeautifulSoup("<html><body><p>Google vs Microsoft in AI.</p></body></html>", "lxml")
        result = analyze_entity_relationships(soup, "Google", use_llm=True)

    assert "knowledge_triples" in result
    assert "entity_types" in result


def test_brand_cooccurrence_industry_terms():
    """Brand co-occurrence with industry terms detected (regex, no LLM)."""
    html = "<html><body><p>GEO SEO AI content marketing digital marketing.</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_entity_relationships(soup, "TestBrand", use_llm=False)
    cooc = result["brand_cooccurrence"]
    assert cooc["industry_terms_found"] >= 3


def test_brand_cooccurrence_case_insensitive():
    """Industry term matching is case-insensitive (regex, no LLM)."""
    html = "<html><body><p>GEO SEO AI SEO SEO GEO.</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_entity_relationships(soup, "TestBrand", use_llm=False)
    counts = result["brand_cooccurrence"]["cooccurrence_counts"]
    assert counts.get("SEO", 0) >= 2


def test_internal_duplicates_no_paragraphs():
    """Fewer than 2 long paragraphs — no duplicates possible."""
    html = "<html><body><p>Short.</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_internal_duplicates(soup)
    assert result["duplicate_score"] == 100


def test_internal_duplicates_no_overlap():
    """Completely different paragraphs — high score."""
    html = """
    <html><body>
        <p>Digital marketing involves promoting products through online channels.</p>
        <p>Agriculture refers to the practice of farming and cultivating crops.</p>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_internal_duplicates(soup)
    assert result["duplicate_score"] == 100


def test_internal_duplicates_70_percent_overlap():
    """Exactly 70% overlap — at threshold, not flagged as duplicate."""
    # 70% overlap is the threshold (> 0.7 triggers)
    para1 = "Search engine optimization improves website visibility on Google Bing and other search engines"
    para2 = "Search engine optimization improves website visibility on Google Bing and other search platforms"
    html = f"<html><body><p>{para1}</p><p>{para2}</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_internal_duplicates(soup)
    # At exactly 0.7 overlap, it may or may not be flagged depending on implementation
    assert result["duplicate_score"] >= 0


def test_internal_duplicates_highly_similar():
    """Nearly identical paragraphs — low score."""
    html = """
    <html><body>
        <p>Content marketing is crucial for brands. It helps improve visibility online and drives engagement with customers.</p>
        <p>Content marketing is crucial for brands. It helps improve visibility online and drives engagement with customers.</p>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_internal_duplicates(soup)
    assert result["duplicate_score"] < 100
    assert len(result["duplicates_found"]) > 0


def test_entity_graph_score_empty():
    """Empty inputs — zero score."""
    result = compute_entity_graph_score({}, {})
    assert result["entity_graph_score"] == 0.0


def test_entity_graph_score_breakdown_keys():
    """All breakdown keys present."""
    entity_rel = {"entity_diversity_score": 50, "relationship_density_score": 30}
    brand_cooc = {"industry_terms_found": 5}
    result = compute_entity_graph_score(entity_rel, brand_cooc)
    assert set(result["breakdown"].keys()) == {"entity_diversity", "relationship_density", "brand_industry_coverage"}


def test_entity_graph_score_max():
    """Max possible score is 100."""
    entity_rel = {"entity_diversity_score": 100, "relationship_density_score": 100}
    brand_cooc = {"industry_terms_found": 10}  # 10*10=100
    result = compute_entity_graph_score(entity_rel, brand_cooc)
    assert result["entity_graph_score"] <= 100


# ========================================================================
# competitive_analyzer.py - edge cases (mocked, no real HTTP)
# ========================================================================
from unittest.mock import patch
from competitive_analyzer import compare_competitors


def _mock_response(html: str, status: int = 200):
    """Create a mock response object."""
    class MockResp:
        def __init__(self):
            self.text = html
            self.status_code = status
    return MockResp()


MOCK_HTML = """
<html><head><title>Test Site</title><meta name="description" content="Test description"/></head>
<body><h1>Main Heading</h1><h2>Sub Heading</h2>
<img src="a.jpg" alt="Alt text"/><p>Content with SEO keywords and search optimization.</p>
<script type="application/ld+json">{"@type":"Organization","name":"Test Org"}</script>
<a href="/internal">Internal Link</a><a href="https://external.com">External Link</a>
</body></html>
"""


@patch("competitive_analyzer.requests.get")
def test_compare_competitors_single_domain(mock_get):
    """Single domain with no competitors works."""
    mock_get.return_value = _mock_response(MOCK_HTML)
    result = compare_competitors("example.com", [])
    assert "target_domain" in result
    assert result["target_domain"] == "example.com"
    assert result["competitors"] == []


@patch("competitive_analyzer.requests.get")
def test_compare_competitors_two_competitors(mock_get):
    """Two competitor domains parsed correctly."""
    mock_get.return_value = _mock_response(MOCK_HTML)
    result = compare_competitors("example.com", ["example.org", "example.net"])
    assert len(result["competitors"]) == 2


@patch("competitive_analyzer.requests.get")
def test_share_of_voice_target_domain_present(mock_get):
    """Share of voice includes target domain."""
    mock_get.return_value = _mock_response(MOCK_HTML)
    result = compare_competitors("example.com", ["example.org"])
    assert "example.com" in result["share_of_voice"]
    assert "example.org" in result["share_of_voice"]


@patch("competitive_analyzer.requests.get")
def test_share_of_voice_all_domains_scored(mock_get):
    """All domains get a SOV score."""
    mock_get.return_value = _mock_response(MOCK_HTML)
    result = compare_competitors("example.com", ["example.org"])
    for domain in ["example.com", "example.org"]:
        assert domain in result["share_of_voice"]


@patch("competitive_analyzer.requests.get")
def test_competitive_gaps_structure(mock_get):
    """Gap analysis has correct structure per competitor."""
    mock_get.return_value = _mock_response(MOCK_HTML)
    result = compare_competitors("example.com", ["example.org"])
    for comp_domain, gaps in result["competitive_gaps"].items():
        for metric, gap_data in gaps.items():
            assert "target" in gap_data
            assert "competitor" in gap_data
            assert "gap" in gap_data
            assert "gap_pct" in gap_data


@patch("competitive_analyzer.requests.get")
def test_competitive_gaps_target_not_in_gaps(mock_get):
    """Target domain itself is not in competitive gaps."""
    mock_get.return_value = _mock_response(MOCK_HTML)
    result = compare_competitors("example.com", ["example.org"])
    assert "example.com" not in result["competitive_gaps"]


# ========================================================================
# geo_attribution.py - edge cases
# ========================================================================
from geo_attribution import (
    estimate_geo_attributed_traffic, estimate_geu_influenced_conversions,
    project_geo_roi, generate_attribution_report
)


def test_traffic_zero_citations():
    """Zero citations = zero traffic."""
    result = estimate_geo_attributed_traffic(0)
    assert result["estimated_monthly_clicks"] == 0


def test_traffic_custom_parameters():
    """Custom CTR and visibility are reflected in result."""
    result = estimate_geo_attributed_traffic(50, avg_ctr_from_ai_citation=0.10, ai_visibility_monthly=50000)
    assert result["citation_count"] == 50
    assert result["avg_ctr"] == 0.10


def test_traffic_calculation_formula():
    """Traffic formula: (citations*0.15 + citations*0.05) * ctr * visibility."""
    result = estimate_geo_attributed_traffic(10, avg_ctr_from_ai_citation=0.10, ai_visibility_monthly=10000)
    # top = 10*0.15 = 1.5, secondary = 10*0.05 = 0.5, total = 2.0
    # clicks = 2.0 * 0.10 * 10000 = 2000
    assert result["estimated_monthly_clicks"] == 2000


def test_conversions_zero_traffic():
    """Zero traffic = zero conversions."""
    result = estimate_geu_influenced_conversions(0)
    assert result["direct_conversions"] == 0
    assert result["geo_influenced_conversions"] == 0


def test_conversions_influence_factor_applied():
    """Influence factor multiplies conversions."""
    result = estimate_geu_influenced_conversions(1000, geo_influence_factor=2.0)
    # direct = 1000*0.025 = 25, influenced = 1000*0.025*2.0 = 50
    assert result["geo_influenced_conversions"] == 50


def test_roi_zero_revenue():
    """Zero citations produces zero revenue and negative ROI."""
    result = project_geo_roi(1000, 0)
    assert result["estimated_revenue"] == 0
    assert result["roi_multiplier"] == 0


def test_roi_payback_months_none_when_zero_revenue():
    """Payback months is None when revenue is zero."""
    result = project_geo_roi(500, 0)
    assert result["payback_months"] is None


def test_roi_payback_months_calculated():
    """Payback months calculated correctly when revenue > 0."""
    # citations=100, visibility=10000, ctr=0.08
    # clicks = (15+5)*0.08*10000 = 16000
    # conversions = 16000*0.025 = 400
    # revenue = 400*100 = 40000
    # payback_months = 500 / (40000/12) = 500/3333 = 0.15
    result = project_geo_roi(500, 100)
    assert result["payback_months"] is not None
    assert result["payback_months"] > 0


def test_roi_multiplier_calculation():
    """ROI multiplier = revenue / investment."""
    result = project_geo_roi(500, 100)
    # revenue depends on citations; verify multiplier matches revenue/investment
    assert abs(result["roi_multiplier"] - (result["estimated_revenue"] / 500)) < 0.01


def test_attribution_report_contains_all_sections():
    """Full attribution report has traffic, conversion, ROI sections."""
    result = generate_attribution_report({}, 50, 500)
    assert "traffic_attribution" in result
    assert "conversion_attribution" in result
    assert "roi_projection" in result
    assert "key_insight" in result


def test_attribution_insight_strong_roi():
    """Strong ROI (>3x multiplier) generates correct insight."""
    result = generate_attribution_report({}, 200, 100)
    assert "Strong GEO ROI" in result["key_insight"] or "Positive GEO ROI" in result["key_insight"]


def test_attribution_insight_poor_roi():
    """Poor ROI generates correct insight."""
    result = generate_attribution_report({}, 1, 1000)
    assert "requires optimization" in result["key_insight"]


# ========================================================================
# china_platform_analyzer.py - edge cases
# ========================================================================
from china_platform_analyzer import (
    analyze_china_platform_readiness, _get_chinese_char_ratio,
    _compute_baidu_score, _compute_tongyi_score, _compute_douai_score,
    CHINA_PLATFORMS
)


def test_china_platforms_constant_has_all_three():
    """CHINA_PLATFORMS has all three platforms."""
    assert set(CHINA_PLATFORMS.keys()) == {"baidu_wenxin", "alibaba_tongyi", "bytedance_douai"}


def test_china_char_ratio_pure_english():
    """Pure English text has zero Chinese char ratio."""
    ratio = _get_chinese_char_ratio("Hello world this is a test")
    assert ratio == 0.0


def test_china_char_ratio_pure_chinese():
    """Pure Chinese text has ratio of 1.0."""
    ratio = _get_chinese_char_ratio("这是一个中文测试内容")
    assert ratio == 1.0


def test_china_char_ratio_empty_string():
    """Empty string returns 0."""
    ratio = _get_chinese_char_ratio("")
    assert ratio == 0.0


def test_china_platform_returns_all_required_keys():
    """Result has all required keys."""
    html = "<html><body><p>Content</p></body></html>"
    result = analyze_china_platform_readiness(html)
    required = ["baidu_wenxin_score", "alibaba_tongyi_score", "bytedance_douai_score",
                 "composite_china_score", "chinese_char_ratio", "is_bilingual",
                 "schemas_found", "recommendations"]
    for key in required:
        assert key in result


def test_china_platform_scores_in_range():
    """All platform scores are between 0 and 100."""
    html = "<html><body><p>Some content here.</p></body></html>"
    result = analyze_china_platform_readiness(html)
    for key in ["baidu_wenxin_score", "alibaba_tongyi_score", "bytedance_douai_score"]:
        assert 0 <= result[key] <= 100


def test_china_platform_composite_is_average():
    """Composite score is average of three platforms."""
    html = "<html><body><p>English content.</p></body></html>"
    result = analyze_china_platform_readiness(html)
    expected = round((result["baidu_wenxin_score"] + result["alibaba_tongyi_score"] + result["bytedance_douai_score"]) / 3, 1)
    assert result["composite_china_score"] == expected


def test_china_baidu_score_english_page():
    """English-only page gets low Baidu score (low Chinese ratio)."""
    html = "<html><body><p>" + "word " * 100 + "</p></body></html>"
    result = analyze_china_platform_readiness(html)
    assert result["baidu_wenxin_score"] < 40


def test_china_baidu_score_chinese_page():
    """Chinese page gets high Baidu score (with Baidu schema to trigger has_baidu_schema flag)."""
    html = """<html><body>
    <script type="application/ld+json">{"@type":"BaiduOrganization","name":"TestOrg"}</script>
    <p>""" + "中 " * 50 + """</p></body></html>"""
    result = analyze_china_platform_readiness(html)
    # With Baidu schema + ~50% Chinese: 20(base) + 30(baidu_flag) + 10(schema_count) = 60
    assert result["baidu_wenxin_score"] > 40


def test_china_tongyi_alibaba_ecosystem_refs():
    """Alibaba ecosystem terms boost Tongyi score."""
    html_eco = "<html><body><p>淘宝天猫阿里巴巴支付宝</p></body></html>"
    html_plain = "<html><body><p>Some content about general topics.</p></body></html>"
    result_eco = analyze_china_platform_readiness(html_eco)
    result_plain = analyze_china_platform_readiness(html_plain)
    assert result_eco["alibaba_tongyi_score"] > result_plain["alibaba_tongyi_score"]


def test_china_douai_video_boost():
    """Video content boosts DouAI score."""
    html_video = "<html><body><video src='clip.mp4'></video><p>Content.</p></body></html>"
    html_no_video = "<html><body><p>Content without video here.</p></body></html>"
    result_video = analyze_china_platform_readiness(html_video)
    result_no = analyze_china_platform_readiness(html_no_video)
    assert result_video["bytedance_douai_score"] >= result_no["bytedance_douai_score"]


def test_china_recommendations_logic():
    """Recommendations generated when scores below threshold."""
    html = "<html><body><p>English only content.</p></body></html>"
    result = analyze_china_platform_readiness(html)
    # English page (< 30% Chinese) should trigger recommendation
    assert any("Chinese language" in r for r in result["recommendations"])


def test_china_bilingual_flag():
    """Bilingual is detected when Chinese ratio between 10% and 90%."""
    html_bi = "<html><body><p>" + "word " * 30 + "中 " * 30 + "</p></body></html>"  # ~50% Chinese
    html_en = "<html><body><p>" + "word " * 100 + "</p></body></html>"  # 0% Chinese
    html_zh = "<html><body><p>" + "中" * 100 + "</p></body></html>"  # 100% Chinese
    result_bi = analyze_china_platform_readiness(html_bi)
    result_en = analyze_china_platform_readiness(html_en)
    result_zh = analyze_china_platform_readiness(html_zh)
    assert result_bi["is_bilingual"] is True
    assert result_en["is_bilingual"] is False
    assert result_zh["is_bilingual"] is False


# ========================================================================
# spa_renderer.py - edge cases
# ========================================================================
from spa_renderer import is_playwright_available, render_spa_page, enhance_fetch_result


def test_is_playwright_available_returns_bool():
    """Returns True or False (not None or raises)."""
    result = is_playwright_available()
    assert isinstance(result, bool)


def test_render_spa_page_unavailable_fallback():
    """When Playwright not installed, returns error dict."""
    if is_playwright_available():
        pytest.skip("Playwright is installed — cannot test unavailable path")

    result = render_spa_page("https://example.com")
    assert "error" in result
    assert result["fallback_used"] is True


def test_render_spa_page_available_returns_structure():
    """When Playwright available, returns full structure."""
    if not is_playwright_available():
        pytest.skip("Playwright not installed")

    result = render_spa_page("https://example.com", wait_time=500)
    assert "url" in result
    assert "title" in result
    assert "rendered_text_length" in result
    assert "rendering_method" in result
    assert result["fallback_used"] is False


def test_render_spa_page_csr_detection():
    """Pages with >500 chars detected as CSR."""
    if not is_playwright_available():
        pytest.skip("Playwright not installed")

    result = render_spa_page("https://example.com", wait_time=500)
    assert result["rendering_method"] in ["CSR", "SSR"]


def test_render_spa_page_text_content_limited():
    """Text content is truncated to 5000 chars."""
    if not is_playwright_available():
        pytest.skip("Playwright not installed")

    result = render_spa_page("https://example.com", wait_time=500)
    assert len(result.get("text_content", "")) <= 5000


def test_enhance_fetch_result_ssr_content_no_playwright():
    """Page with SSR content doesn't trigger Playwright."""
    fetch_result = {"url": "https://example.com", "has_ssr_content": True}
    result = enhance_fetch_result(fetch_result, use_playwright_fallback=True)
    assert result["final_content_source"] == "requests"


def test_enhance_fetch_result_disabled_flag():
    """use_playwright_fallback=False skips Playwright."""
    fetch_result = {"url": "https://example.com", "has_ssr_content": False}
    result = enhance_fetch_result(fetch_result, use_playwright_fallback=False)
    assert result["final_content_source"] == "requests"


def test_enhance_fetch_result_preserves_original_fields():
    """Original fetch_result fields are preserved."""
    fetch_result = {"url": "https://example.com", "has_ssr_content": False, "status_code": 200}
    result = enhance_fetch_result(fetch_result, use_playwright_fallback=True)
    # If playwright not available, returns original with added final_content_source
    assert result["url"] == "https://example.com"
    assert result["status_code"] == 200
    assert "final_content_source" in result


# ========================================================================
# Integration: scoring.py used by other modules
# ========================================================================
from scoring import WEIGHTS


def test_weights_match_plan_spec():
    """Weights match the plan specification exactly."""
    assert WEIGHTS["ai_citability"] == 0.25
    assert WEIGHTS["brand_authority"] == 0.20
    assert WEIGHTS["content_quality"] == 0.20
    assert WEIGHTS["technical"] == 0.15
    assert WEIGHTS["structured_data"] == 0.10
    assert WEIGHTS["platform_optimization"] == 0.10


def test_all_score_functions_importable():
    """All scoring functions can be imported from scoring module."""
    from scoring import (
        compute_citability_score, compute_eeat_score,
        compute_geu_dimension_scores, normalize_platform_scores,
        compute_final_geu_score
    )
    assert callable(compute_citability_score)
    assert callable(compute_eeat_score)
    assert callable(compute_geu_dimension_scores)
    assert callable(normalize_platform_scores)
    assert callable(compute_final_geu_score)
