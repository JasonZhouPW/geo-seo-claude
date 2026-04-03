#!/usr/bin/env python3
"""
GEU (Generative Engine Utility) Evaluator

Evaluates rewritten content quality using LLM-based assessment.
Based on AutoGEO research (ICLR 2026).

Usage:
    python geu_evaluator.py <url> [--engine gemini|gpt|claude] [--output result.json]
"""

import sys
import os
import json
import argparse
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add script directory to path for autogeo_rules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from autogeo_rules import get_rules_for_audit, get_rules_key
    HAS_AUTOGEO_RULES = True
except ImportError:
    HAS_AUTOGEO_RULES = False
    print("Warning: autogeo_rules not found, using basic rules")

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
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Quality criteria from AutoGEO
QUALITY_CRITERIA = [
    {"name": "Clarity", "description": "Assess how clearly and rigorously the answer is structured. High-quality responses are like in-depth reports with distinct, non-overlapping points and strong logical flow. Penalize redundancy, ambiguity, and filler."},
    {"name": "Depth", "description": "Assess comprehensiveness and analytical depth. Excellent reports show critical thinking and nuance, not just surface-level facts. Word count does not equal depth."},
    {"name": "Balance", "description": "Evaluate fairness and objectivity. Excellent reports present multiple perspectives impartially, especially for controversial topics. Poor reports are biased or one-sided."},
    {"name": "Breadth", "description": "Evaluate how many distinct and relevant subtopics, perspectives, or contexts are covered. Excellent reports provide a wide-ranging yet focused exploration."},
    {"name": "Support", "description": "Evaluate the extent to which key claims are substantiated by credible evidence from the provided text. Claims should be clearly linked to sources. Vague references are unacceptable."},
    {"name": "Insightfulness", "description": "Assess originality and value. Excellent reports go beyond common knowledge, offering original synthesis or thought-provoking connections. Recommendations must be concrete and actionable."}
]

PROMPTS = {
    "quality_evaluator": """You are a strict expert evaluator. Assess the quality of an "Answer" to a "Question" based ONLY on the criterion of **{criterion_name}**.

**Criterion: {criterion_name}**
{criterion_description}

**Question:**
{question}

**Answer:**
{answer}

Provide your rating as a JSON object with two keys:
1. "rating": An integer from 0 (poor) to 10 (excellent).
2. "justification": A brief, harsh justification explaining why the answer earned that rating based on the criterion.

**Do not be generous.** High scores are for outstanding answers.

Your JSON response:""",

    "claim_extractor": """You are an information extraction expert.
Given a report, extract all distinct factual claims. For each claim, identify the source indices it cites (e.g., [0], [1], [2, 3]).

Return a JSON object with a "claims" list, where each entry has:
- "claim_id": A sequential integer starting from 1.
- "claim": A concise, complete sentence of the claim.
- "source_indices": A list of integer indices cited for this claim. If no source is cited, return an empty list [].

**IMPORTANT**:
- Only extract factual claims, not opinions or summaries.
- The source indices must be integers extracted directly from citations like `[0]` or `[1, 2]`.

Report to process:
"""
}


class GEUClient:
    """GEU Evaluator client supporting multiple LLM providers."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider.lower()

        if self.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=key)
            self.model = "gpt-4o-mini"
        elif self.provider == "anthropic" or self.provider == "claude":
            if not HAS_ANTHROPIC:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
            key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = Anthropic(api_key=key)
            self.model = "claude-sonnet-4-5"
        elif self.provider == "gemini":
            key = api_key or os.environ.get("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY not set")
            # Use OpenAI-compatible API or Google's API
            # For now, fallback to OpenAI if using Gemini format
            raise NotImplementedError("Gemini provider requires additional setup")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def call_llm_json(self, prompt: str) -> Optional[Dict]:
        """Call LLM and parse JSON response."""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                return json.loads(content)
            elif self.provider in ("anthropic", "claude"):
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                for block in response.content:
                    # Skip thinking blocks
                    if hasattr(block, 'thinking'):
                        continue
                    if hasattr(block, 'text'):
                        text = block.text.strip()
                        # Handle JSON in code blocks
                        if text.startswith("```"):
                            lines = text.split("\n")
                            json_lines = [l for l in lines if not l.startswith("```")]
                            text = "\n".join(json_lines)
                        return json.loads(text)
                return None
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None

    def extract_claims(self, text: str) -> List[Dict]:
        """Extract claims from text."""
        prompt = PROMPTS["claim_extractor"] + f"\n\"\"\"\n{text}\n\"\"\"\n\nReturn the JSON object and nothing else."
        result = self.call_llm_json(prompt)
        if result and "claims" in result:
            return result["claims"]
        return []

    def evaluate_quality(self, question: str, answer: str) -> Dict[str, float]:
        """Evaluate answer quality across 6 dimensions."""
        scores = {}
        for criterion in QUALITY_CRITERIA:
            prompt = PROMPTS["quality_evaluator"].format(
                criterion_name=criterion["name"],
                criterion_description=criterion["description"],
                question=question,
                answer=answer
            )
            result = self.call_llm_json(prompt)
            if result and "rating" in result:
                scores[criterion["name"]] = result["rating"] / 10.0
            else:
                scores[criterion["name"]] = None
        return scores


def fetch_page_content(url: str, timeout: int = 30) -> Tuple[str, str]:
    """Fetch and extract text content from a webpage using Playwright for JS rendering."""

    # Try Playwright first for JavaScript-rendered sites
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)

            # Extract title
            title_text = page.title()

            # Get main content
            content = page.evaluate("""
                () => {
                    const main = document.querySelector('main') || document.querySelector('article') || document.body;
                    // Remove unwanted elements
                    const toRemove = main.querySelectorAll('script, style, nav, header, footer, aside, .nav, .footer, .header, .menu, .sidebar');
                    toRemove.forEach(el => el.remove());
                    return main ? main.innerText : document.body.innerText;
                }
            """)

            browser.close()

            # Clean up whitespace
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            text = "\n".join(lines)

            return title_text, text[:10000]
    except ImportError:
        pass  # Fall back to requests
    except Exception as e:
        pass  # Fall back to requests

    # Fall back to requests for non-JS sites
    if not HAS_REQUESTS:
        raise ImportError("requests package not installed. Run: pip install requests")

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Extract title
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # Get main content
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        return title_text, text[:10000]
    except Exception as e:
        return "", f"Error fetching page: {str(e)}"


def get_rewrite_prompt(content: str, url: str, business_type: str = "saas", engine: str = "gemini") -> str:
    """Generate an AutoGEO-style rewrite prompt."""
    if not HAS_AUTOGEO_RULES:
        return f"Rewrite the following content for better AI citability:\n\n{content}"

    rules = get_rules_for_audit(business_type, engine)
    rules_string = "- " + "\n- ".join(rules[:10])

    prompt = f"""You are given a website document as a source. This source, along with other sources, will be used by a language model (LLM) to generate answers to user questions, with each line in the generated answer being cited with its original source. Your task, as the owner of the source, is to **rewrite your document in a way that maximizes its visibility and impact in the LLM's final answer, ensuring your source is more likely to be quoted and cited**.

You can regenerate the provided source so that it strictly adheres to the "Quality Guidelines", and you can also apply any other methods or techniques, as long as they help your rewritten source text rank higher in terms of relevance, authority, and impact in the LLM's generated answers.

## Source URL
{url}

## Quality Guidelines to Follow:

{rules_string}

## Original Content:
{content}

## Rewritten Content:
"""
    return prompt


def call_llm_rewrite(prompt: str, provider: str = "openai") -> str:
    """Call LLM to rewrite content."""
    try:
        if provider == "openai":
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            model = "gpt-4o-mini"
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096
            )
            return response.choices[0].message.content
        elif provider in ("anthropic", "claude"):
            client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
            model = "claude-sonnet-4-5"
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
            return ""
    except Exception as e:
        return f"[Error calling LLM: {str(e)}]"


def detect_business_type(title: str, content: str) -> str:
    """Detect business type from content."""
    text = (title + " " + content).lower()
    ecommerce_signals = ["price", "buy", "shop", "cart", "checkout", "product", "add to cart", "sale", "discount", "order", "payment"]
    ecommerce_count = sum(1 for signal in ecommerce_signals if signal in text)
    return "ecommerce" if ecommerce_count >= 3 else "saas"


def evaluate_geu(
    url: str,
    provider: str = "openai",
    business_type: Optional[str] = None,
    skip_rewrite: bool = False,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """Main GEU evaluation function."""

    print(f"Fetching: {url}")
    title, content = fetch_page_content(url)

    if not content or content.startswith("Error"):
        return {"error": content}

    print(f"Title: {title}")
    print(f"Content length: {len(content)} characters")

    # Detect business type
    if not business_type:
        business_type = detect_business_type(title, content)
    print(f"Detected business type: {business_type}")

    # Generate rewrite prompt
    engine_name = "gpt" if provider == "openai" else "claude" if provider in ("anthropic", "claude") else "gemini"
    rewrite_prompt = get_rewrite_prompt(content, url, business_type, engine_name)

    if skip_rewrite:
        print("\nSkipping rewrite (--skip-rewrite flag set)")
        rewritten_content = content
    else:
        print("\nGenerating rewritten content...")
        rewritten_content = call_llm_rewrite(rewrite_prompt, provider)
        if rewritten_content.startswith("[Error"):
            print(f"Rewrite error: {rewritten_content}")
            print("Falling back to original content for evaluation")
            rewritten_content = content

    print(f"Rewritten content length: {len(rewritten_content)} characters")

    # Evaluate with GEU client
    print(f"\nEvaluating quality with {provider}...")
    geu_client = GEUClient(provider=provider)

    # Use the rewritten content as the "answer"
    question = f"What is the main content and purpose of {url}?"

    print("Calculating quality dimensions...")
    quality_scores = geu_client.evaluate_quality(question, rewritten_content)

    # Extract claims
    print("Extracting claims...")
    claims = geu_client.extract_claims(rewritten_content)

    # Calculate overall score
    valid_scores = [s for s in quality_scores.values() if s is not None]
    overall_quality = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    # Calculate citation metrics
    total_claims = len(claims)
    cited_claims = [c for c in claims if c.get("source_indices")]
    citation_recall = len(cited_claims) / total_claims if total_claims > 0 else 0

    result = {
        "url": url,
        "title": title,
        "business_type": business_type,
        "provider": provider,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content_length": len(content),
        "rewritten_length": len(rewritten_content),
        "quality_dimensions": {
            "clarity": quality_scores.get("Clarity"),
            "depth": quality_scores.get("Depth"),
            "balance": quality_scores.get("Balance"),
            "breadth": quality_scores.get("Breadth"),
            "support": quality_scores.get("Support"),
            "insightfulness": quality_scores.get("Insightfulness")
        },
        "citation_metrics": {
            "total_claims": total_claims,
            "cited_claims": len(cited_claims),
            "citation_recall": citation_recall
        },
        "overall_quality_score": round(overall_quality, 3),
        "claims_sample": claims[:5] if claims else [],
        "rewritten_content": rewritten_content[:2000] + "..." if len(rewritten_content) > 2000 else rewritten_content
    }

    # Save to file
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_file}")

    # Save rewritten content to file
    rewrite_file = output_file.replace('.json', '-rewritten.md') if output_file else 'rewrite-content.md'
    if not skip_rewrite and rewritten_content:
        with open(rewrite_file, 'w', encoding='utf-8') as f:
            f.write(f"# Rewritten Content for {url}\n\n")
            f.write(f"Original length: {len(content)} chars\n")
            f.write(f"Rewritten length: {len(rewritten_content)} chars\n\n")
            f.write("---\n\n")
            f.write(rewritten_content)
        print(f"Rewritten content saved to: {rewrite_file}")

    # Print summary
    print("\n" + "="*60)
    print("GEU EVALUATION RESULTS")
    print("="*60)
    print(f"URL: {url}")
    print(f"Provider: {provider}")
    print(f"Overall Quality Score: {overall_quality:.3f}")
    print("\nQuality Dimensions:")
    for dim, score in quality_scores.items():
        if score is not None:
            print(f"  {dim}: {score:.3f}")
        else:
            print(f"  {dim}: N/A")
    print(f"\nCitation Recall: {citation_recall:.3f} ({len(cited_claims)}/{total_claims} claims cited)")
    print("="*60)

    return result


def main():
    parser = argparse.ArgumentParser(description="GEU Evaluator - Evaluate content quality using LLM assessment")
    parser.add_argument("url", help="URL of the page to evaluate")
    parser.add_argument("--provider", "-p", default="openai",
                        choices=["openai", "anthropic", "claude", "gemini"],
                        help="LLM provider to use (default: openai)")
    parser.add_argument("--engine", "-e", default="gemini",
                        help="Target AI engine for rewrite (default: gemini)")
    parser.add_argument("--skip-rewrite", "-s", action="store_true",
                        help="Skip rewriting, evaluate original content only")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--business-type", "-b",
                        choices=["saas", "ecommerce", "local", "publisher", "agency", "other"],
                        help="Business type override")

    args = parser.parse_args()

    result = evaluate_geu(
        url=args.url,
        provider=args.provider,
        business_type=args.business_type,
        skip_rewrite=args.skip_rewrite,
        output_file=args.output
    )

    if result.get("error"):
        print(f"\nError: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
