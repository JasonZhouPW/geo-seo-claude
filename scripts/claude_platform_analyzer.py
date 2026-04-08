#!/usr/bin/env python3
"""
Claude Platform Analyzer — Analyzes content readiness for Claude (Anthropic) citations.
"""

import sys
import re
from typing import Dict, List
from bs4 import BeautifulSoup


def analyze_claude_readiness(html_content: str) -> Dict:
    """Analyze content readiness for Claude citations."""
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=" ", strip=True)

    passage_analysis = _analyze_passages_for_claude(soup)
    authority_signals = _analyze_authority_signals(soup)
    structure_score = _analyze_structure_for_claude(soup, text)
    citation_compat = _analyze_citation_compatibility(soup)

    score = (
        passage_analysis["passage_quality_score"] * 0.30 +
        authority_signals["authority_score"] * 0.30 +
        structure_score * 0.25 +
        citation_compat["citation_readiness"] * 0.15
    )

    return {
        "claude_readiness_score": round(score, 1),
        "passage_analysis": passage_analysis,
        "authority_signals": authority_signals,
        "structure_score": round(structure_score, 1),
        "citation_compatibility": citation_compat,
        "recommendations": _claude_recommendations(passage_analysis, authority_signals, structure_score),
    }


def _analyze_passages_for_claude(soup: BeautifulSoup) -> Dict:
    paragraphs = soup.find_all("p")
    good_passages = 0
    optimal_length_passages = 0
    total_words = 0

    for p in paragraphs:
        text = p.get_text(strip=True)
        words = len(text.split())
        total_words += words
        if words >= 50:
            good_passages += 1
        if 150 <= words <= 250:
            optimal_length_passages += 1

    passage_quality = 0
    if paragraphs:
        ratio = optimal_length_passages / len(paragraphs)
        passage_quality = min(100, ratio * 100 + (good_passages / len(paragraphs)) * 30)

    return {
        "total_paragraphs": len(paragraphs),
        "good_passages": good_passages,
        "optimal_length_passages": optimal_length_passages,
        "passage_quality_score": round(passage_quality, 1),
        "avg_paragraph_words": round(total_words / len(paragraphs), 1) if paragraphs else 0,
    }


def _analyze_authority_signals(soup: BeautifulSoup) -> Dict:
    score = 0
    signals_found = []

    author_tags = soup.find_all(["a", "span", "div"], class_=re.compile(r"author|byline", re.I))
    if author_tags:
        score += 25
        signals_found.append("author_info")

    cred_patterns = [
        r"\d+\+?\s*(?:years|yr)\s+(?:of\s+)?experience",
        r"Ph\.?D\.?|M\.?D\.?|MBA",
        r"(?:certified|licensed|accredited)",
        r"founder|CEO|CTO|Director",
    ]
    page_text = soup.get_text()
    for pattern in cred_patterns:
        if re.search(pattern, page_text, re.I):
            score += 10
            signals_found.append(f"credential")
            break

    if soup.find(["ol", "ul"], class_=re.compile(r"reference|citation|bibliography", re.I)):
        score += 20
        signals_found.append("references_section")

    about_links = soup.find_all("a", href=re.compile(r"about|bio|author", re.I))
    if about_links:
        score += 15
        signals_found.append("about_page_link")

    time_tags = soup.find_all("time")
    if time_tags:
        score += 10
        signals_found.append("publish_date")

    return {
        "authority_score": round(min(100, score), 1),
        "signals_found": signals_found,
    }


def _analyze_structure_for_claude(soup: BeautifulSoup, text: str) -> float:
    score = 0

    h1_count = len(soup.find_all("h1"))
    h2_count = len(soup.find_all("h2"))

    if 1 <= h1_count <= 2:
        score += 20
    if h2_count >= 3:
        score += 20

    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    if headings:
        score += min(20, len(headings) * 3)

    lists = soup.find_all(["ul", "ol"])
    if lists:
        score += min(20, len(lists) * 5)

    sentences = re.split(r"[.!?]+", text)
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
    if 10 <= avg_sentence_len <= 25:
        score += 20

    return min(100, score)


def _analyze_citation_compatibility(soup: BeautifulSoup) -> Dict:
    external_links = []
    for a in soup.find_all("a", href=re.compile(r"^https?://")):
        href = a.get("href", "")
        if href and not href.startswith(("http://localhost", "http://127.")):
            external_links.append(a)

    has_citations = len(external_links) >= 3
    quotes = soup.find_all(["blockquote", "q"])
    has_quotes = len(quotes) > 0

    page_text = soup.get_text()
    stat_matches = re.findall(r"\d+\.?\d*%", page_text)
    stat_count = len(stat_matches)

    citation_readiness = 0
    if has_citations:
        citation_readiness += 40
    if has_quotes:
        citation_readiness += 30
    if stat_count >= 2:
        citation_readiness += 30

    return {
        "citation_readiness": round(min(100, citation_readiness), 1),
        "external_links_count": len(external_links),
        "quote_blocks": len(quotes),
        "statistics_mentioned": stat_count,
    }


def _claude_recommendations(passage: Dict, authority: Dict, structure: float) -> List[str]:
    recs = []
    if passage["passage_quality_score"] < 60:
        recs.append("Expand paragraphs to 150-250 words for better Claude passage extraction")
    if authority["authority_score"] < 50:
        recs.append("Add author credentials and expertise indicators (years of experience, certifications)")
    if structure < 50:
        recs.append("Improve heading hierarchy — use H2/H3 to organize content logically")
    if passage["avg_paragraph_words"] < 100:
        recs.append("Add 3+ paragraphs of 100+ words with substantive reasoning")
    return recs


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) > 1:
        import requests
        url = sys.argv[1]
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        result = analyze_claude_readiness(resp.text)
    else:
        result = {"error": "Usage: python claude_platform_analyzer.py <url>"}
    print(json.dumps(result, indent=2, ensure_ascii=False))