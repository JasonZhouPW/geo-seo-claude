#!/usr/bin/env python3
"""
GEO Impression Score Calculator

Based on AutoGEO's GEO Score methodology (ICLR 2026).
Calculates how visible content is in LLM-generated answers based on
citation position, frequency, and word count.

Usage:
    python geo_impression_score.py <url> [--query "your question"]
"""

import sys
import os
import re
import math
import argparse
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Optional: for actual LLM calls
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


@dataclass
class ImpressionScore:
    """Result of impression score calculation."""
    position_score: float
    word_count_score: float
    combined_score: float
    citation_count: int
    avg_position: float
    recommendations: List[str]


def get_num_words(line: List[str]) -> int:
    """Count words longer than 2 characters."""
    return len([x for x in line if len(x) > 2])


def tokenize(text: str) -> List[str]:
    """Simple word tokenizer."""
    # Simple split on whitespace and punctuation
    words = re.findall(r'\b\w+\b', text)
    return words


def extract_citations(text: str) -> List[Tuple[int, str]]:
    """
    Extract citations from text.

    Args:
        text: Text containing citations in [n] format

    Returns:
        List of (citation_index_0based, sentence) tuples
        Note: citation [1] in text -> index 0, [2] -> index 1, etc.
    """
    # Split into sentences (simple approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    citations = []
    citation_pattern = r'\[[^\w\s]*(\d+)[^\w\s]*\]'

    for i, sentence in enumerate(sentences):
        matches = re.findall(citation_pattern, sentence)
        for match in matches:
            # Convert to 0-indexed
            citations.append((int(match) - 1, sentence.strip()))

    return citations


def impression_wordpos_score(citations: List[Tuple[int, str]], n_docs: int = 5) -> List[float]:
    """
    Calculate impression score based on position and word count.

    AutoGEO methodology:
    - Earlier citations get higher scores (exponential decay)
    - More words = higher score
    - Score divided among multiple citations in same sentence

    Args:
        citations: List of (doc_index, sentence) tuples
        n_docs: Number of documents being compared

    Returns:
        List of scores for each document
    """
    if not citations:
        return [1.0 / n_docs] * n_docs

    scores = [0.0] * n_docs
    total_sentences = len(set(cit[1] for cit in citations))

    if total_sentences == 0:
        return [1.0 / n_docs] * n_docs

    for doc_idx, sentence in citations:
        if doc_idx >= n_docs:
            continue

        words = tokenize(sentence)
        word_count = get_num_words(words)

        # Position factor: exponential decay
        # Assuming citations are in order of appearance
        cit_positions = [i for i, (d, s) in enumerate(citations) if d == doc_idx]
        if cit_positions:
            first_pos = min(cit_positions)
            position_factor = math.exp(-1 * first_pos / max(total_sentences - 1, 1))
        else:
            position_factor = 1.0

        # Word count factor
        score = word_count * position_factor

        # Divide by number of citations in this sentence
        same_sent_cits = sum(1 for d, s in citations if s == sentence)
        score /= same_sent_cits

        scores[doc_idx] += score

    # Normalize
    total = sum(scores)
    if total > 0:
        scores = [s / total for s in scores]
    else:
        scores = [1.0 / n_docs] * n_docs

    return scores


def impression_word_count_score(citations: List[Tuple[int, str]], n_docs: int = 5) -> List[float]:
    """
    Calculate impression score based on word count only.

    Args:
        citations: List of (doc_index, sentence) tuples
        n_docs: Number of documents

    Returns:
        List of scores for each document
    """
    if not citations:
        return [1.0 / n_docs] * n_docs

    scores = [0.0] * n_docs

    for doc_idx, sentence in citations:
        if doc_idx >= n_docs:
            continue

        words = tokenize(sentence)
        word_count = get_num_words(words)

        # Divide by citations in sentence
        same_sent_cits = sum(1 for d, s in citations if s == sentence)
        scores[doc_idx] += word_count / same_sent_cits

    # Normalize
    total = sum(scores)
    if total > 0:
        scores = [s / total for s in scores]
    else:
        scores = [1.0 / n_docs] * n_docs

    return scores


def impression_position_score(citations: List[Tuple[int, str]], n_docs: int = 5) -> List[float]:
    """
    Calculate impression score based on position only.

    Args:
        citations: List of (doc_index, sentence) tuples
        n_docs: Number of documents

    Returns:
        List of scores for each document
    """
    if not citations:
        return [1.0 / n_docs] * n_docs

    scores = [0.0] * n_docs
    total_sentences = len(set(cit[1] for cit in citations))

    if total_sentences == 0:
        return [1.0 / n_docs] * n_docs

    for doc_idx, sentence in citations:
        if doc_idx >= n_docs:
            continue

        # Position factor
        cit_positions = [i for i, (d, s) in enumerate(citations) if d == doc_idx and s == sentence]
        if cit_positions:
            first_pos = min(cit_positions)
            position_factor = math.exp(-1 * first_pos / max(total_sentences - 1, 1))
        else:
            position_factor = 1.0

        # Divide by citations in sentence
        same_sent_cits = sum(1 for d, s in citations if s == sentence)
        scores[doc_idx] += position_factor / same_sent_cits

    # Normalize
    total = sum(scores)
    if total > 0:
        scores = [s / total for s in scores]
    else:
        scores = [1.0 / n_docs] * n_docs

    return scores


def calculate_impression_score(
    answer_with_citations: str,
    n_docs: int = 5
) -> ImpressionScore:
    """
    Calculate impression score from an LLM answer with citations.

    Args:
        answer_with_citations: LLM-generated answer with [1], [2], etc. citations
        n_docs: Number of documents in the answer

    Returns:
        ImpressionScore object with scores and recommendations
    """
    citations = extract_citations(answer_with_citations)

    if not citations:
        return ImpressionScore(
            position_score=0.0,
            word_count_score=0.0,
            combined_score=0.0,
            citation_count=0,
            avg_position=0.0,
            recommendations=["No citations found in answer"]
        )

    # Calculate different scores
    pos_scores = impression_position_score(citations, n_docs)
    word_scores = impression_word_count_score(citations, n_docs)
    combined_scores = impression_wordpos_score(citations, n_docs)

    # Calculate average position
    positions = []
    for i, (doc_idx, sentence) in enumerate(citations):
        if doc_idx < n_docs:
            positions.append(i)
    avg_pos = sum(positions) / len(positions) if positions else 0

    # Generate recommendations
    recommendations = []

    doc0_score = combined_scores[0] if n_docs > 0 else 0

    if doc0_score < 0.2:
        recommendations.append("Your document has low visibility. Add more specific details and data.")
    if doc0_score > 0.5:
        recommendations.append("Strong visibility! Maintain citation-friendly structure.")

    if avg_pos > 5:
        recommendations.append("Move key information earlier in the document for better position scoring.")

    # Check word count contribution
    total_words = sum(get_num_words(tokenize(s)) for _, s in citations)
    if total_words < 50:
        recommendations.append("Add more substantive content with specific facts and statistics.")

    return ImpressionScore(
        position_score=pos_scores[0] if n_docs > 0 else 0,
        word_count_score=word_scores[0] if n_docs > 0 else 0,
        combined_score=combined_scores[0] if n_docs > 0 else 0,
        citation_count=len(citations),
        avg_position=avg_pos,
        recommendations=recommendations
    )


def fetch_page_title(url: str) -> str:
    """Fetch page title."""
    if not HAS_REQUESTS:
        return ""

    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        soup = resp.text
        title_match = re.search(r'<title>([^<]+)</title>', soup, re.IGNORECASE)
        return title_match.group(1) if title_match else ""
    except:
        return ""


def demo_score_calculation() -> ImpressionScore:
    """
    Demo with sample citations to show how the scoring works.
    """
    # Sample answer with citations (simulating LLM response)
    sample_answer = """
    According to the research, machine learning has grown significantly [1].
    The study shows that neural networks achieve 95% accuracy on image classification tasks [2].
    Deep learning models have revolutionized computer vision applications [1].
    Natural language processing has seen major advances with transformer architectures [3].
    The data indicates a 40% improvement in performance metrics [2].
    """

    return calculate_impression_score(sample_answer, n_docs=3)


def main():
    parser = argparse.ArgumentParser(
        description="GEO Impression Score Calculator"
    )
    parser.add_argument("url", nargs="?", help="URL to analyze")
    parser.add_argument("--query", "-q", default="What is this page about?",
                        help="Query to ask about the page")
    parser.add_argument("--n-docs", "-n", type=int, default=5,
                        help="Number of documents in comparison (default: 5)")
    parser.add_argument("--demo", "-d", action="store_true",
                        help="Run demo with sample citations")

    args = parser.parse_args()

    if args.demo or args.url is None:
        print("Running demo with sample citations...")
        print("=" * 50)
        sample = """
        According to the research, machine learning has grown significantly [1].
        The study shows that neural networks achieve 95% accuracy on image classification [2].
        Deep learning has revolutionized computer vision [1].
        NLP has advanced with transformer architectures [3].
        Data shows 40% improvement in performance metrics [2].
        """
        print(f"Sample answer:\n{sample}")
        print("=" * 50)

        score = calculate_impression_score(sample, n_docs=3)
        print(f"\nImpression Scores (Doc 1 = target):")
        print(f"  Position Score: {score.position_score:.3f}")
        print(f"  Word Count Score: {score.word_count_score:.3f}")
        print(f"  Combined Score: {score.combined_score:.3f}")
        print(f"  Citation Count: {score.citation_count}")
        print(f"  Avg Position: {score.avg_position:.1f}")
        print(f"\nRecommendations:")
        for rec in score.recommendations:
            print(f"  - {rec}")
        return

    print(f"URL: {args.url}")
    print(f"Query: {args.query}")
    print(f"\nNote: Actual LLM citation extraction requires API integration.")
    print("Use --demo to see how the scoring methodology works.\n")

    # For now, just show the methodology
    print("To use with actual content:")
    print("1. Fetch page content")
    print("2. Call LLM with query and content")
    print("3. Pass LLM response with [1], [2] citations to calculate_impression_score()")
    print("\nExample API integration:")

    example_code = '''
    # Example usage
    answer = call_llm_with_citations(
        query="What is this company about?",
        documents=[content],
        engine="gemini"
    )

    score = calculate_impression_score(answer, n_docs=1)
    print(f"GEO Visibility Score: {score.combined_score:.2f}")
    '''
    print(example_code)


if __name__ == "__main__":
    main()
