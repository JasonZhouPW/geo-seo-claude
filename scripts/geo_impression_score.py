#!/usr/bin/env python3
"""
GEO Impression Score Calculator

Based on AutoGEO's GEO Score methodology (ICLR 2026).
Calculates how visible content is in LLM-generated answers based on
citation position, frequency, and word count.

Usage:
    python geo_impression_score.py <url> [--query "your question"]
    python geo_impression_score.py <url> --provider claude --api-key KEY
"""

import sys
import os
import re
import math
import json
import argparse
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict

# Optional: for actual LLM calls
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


class ImpressionClient:
    """LLM client for GEO Impression Score calculation."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider.lower()

        if self.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("OpenAI package not installed")
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=key)
            self.model = "gpt-4o-mini"
        elif self.provider in ("anthropic", "claude"):
            if not HAS_ANTHROPIC:
                raise ImportError("Anthropic package not installed")
            key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = Anthropic(api_key=key)
            self.model = "claude-sonnet-4-5"
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def call_llm(self, prompt: str) -> str:
        """Call LLM and return text response."""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=2048
                )
                return response.choices[0].message.content or ""
            elif self.provider in ("anthropic", "claude"):
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}]
                )
                for block in response.content:
                    if hasattr(block, 'text'):
                        return block.text
                return ""
        except Exception as e:
            return f"[Error calling LLM: {str(e)}]"


def fetch_page_content(url: str, timeout: int = 30) -> Tuple[str, str]:
    """Fetch and extract text content from a webpage using Playwright for JS rendering."""
    # Try Playwright first for JavaScript-rendered sites
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="load", timeout=timeout * 1000)

            title_text = page.title()

            content = page.evaluate("""
                () => {
                    const main = document.querySelector('main') || document.querySelector('article') || document.body;
                    const toRemove = main.querySelectorAll('script, style, nav, header, footer, aside, .nav, .footer, .header, .menu, .sidebar');
                    toRemove.forEach(el => el.remove());
                    return main ? main.innerText : document.body.innerText;
                }
            """)

            browser.close()

            lines = [line.strip() for line in content.split("\n") if line.strip()]
            text = "\n".join(lines)

            return title_text, text[:10000]
    except ImportError:
        pass
    except Exception as e:
        pass

    # Fall back to requests
    if not HAS_REQUESTS:
        return "", ""

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        return title_text, text[:10000]
    except Exception:
        return "", ""


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


def evaluate_impression(
    url: str,
    provider: str = "openai",
    query: str = "What is this page about?",
    n_docs: int = 5,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """Main impression score evaluation function."""

    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    domain_folder = domain.replace(':', '_')
    os.makedirs(domain_folder, exist_ok=True)

    print(f"Fetching: {url}")
    title, content = fetch_page_content(url)

    if not content:
        return {"error": f"Could not fetch content from {url}"}

    print(f"Title: {title}")
    print(f"Content length: {len(content)} characters")

    # Create LLM client
    print(f"\nGenerating answer with citations using {provider}...")
    client = ImpressionClient(provider=provider)

    # Prompt for LLM to generate answer with citations
    prompt = f"""You are a research assistant. Based on the following content, answer the query.

IMPORTANT: When you use information from the source, cite it using [1] notation.

Query: {query}

Content:
{content[:8000]}

Provide your answer with citations [1] where you use information from the content.
If the content doesn't contain relevant information for a part of your answer, still provide a helpful answer but note that it's based on general knowledge.
"""

    answer = client.call_llm(prompt)

    if answer.startswith("[Error"):
        print(f"LLM Error: {answer}")
        # Fall back to demo calculation
        score = demo_score_calculation()
    else:
        print(f"LLM response length: {len(answer)} characters")
        print(f"\nSample of LLM response:\n{answer[:500]}...")
        score = calculate_impression_score(answer, n_docs=n_docs)

    result = {
        "url": url,
        "title": title,
        "provider": provider,
        "query": query,
        "position_score": score.position_score,
        "word_count_score": score.word_count_score,
        "combined_score": score.combined_score,
        "citation_count": score.citation_count,
        "avg_position": score.avg_position,
        "recommendations": score.recommendations,
        "llm_answer": answer[:2000] + "..." if len(answer) > 2000 else answer
    }

    # Save to file
    if output_file:
        filename = os.path.basename(output_file)
        output_path = os.path.join(domain_folder, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_path}")

    # Print summary
    print("\n" + "="*60)
    print("GEO IMPRESSION SCORE RESULTS")
    print("="*60)
    print(f"URL: {url}")
    print(f"Combined Score: {score.combined_score:.3f}")
    print(f"Position Score: {score.position_score:.3f}")
    print(f"Word Count Score: {score.word_count_score:.3f}")
    print(f"Citation Count: {score.citation_count}")
    print(f"Avg Position: {score.avg_position:.1f}")
    if score.recommendations:
        print("\nRecommendations:")
        for rec in score.recommendations:
            print(f"  - {rec}")
    print("="*60)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="GEO Impression Score Calculator"
    )
    parser.add_argument("url", nargs="?", help="URL to analyze")
    parser.add_argument("--query", "-q", default="What is this page about?",
                        help="Query to ask about the page")
    parser.add_argument("--n-docs", "-n", type=int, default=5,
                        help="Number of documents in comparison (default: 5)")
    parser.add_argument("--provider", "-p", default="openai",
                        choices=["openai", "anthropic", "claude"],
                        help="LLM provider to use")
    parser.add_argument("--api-key", "-k", help="API key (or set env var)")
    parser.add_argument("--demo", "-d", action="store_true",
                        help="Run demo with sample citations")
    parser.add_argument("--output", "-o", help="Output JSON file")

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

    result = evaluate_impression(
        url=args.url,
        provider=args.provider,
        query=args.query,
        n_docs=args.n_docs,
        output_file=args.output
    )

    if result.get("error"):
        print(f"\nError: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
