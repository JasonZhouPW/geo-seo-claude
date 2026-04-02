#!/usr/bin/env python3
"""
GEO Rewrite - AutoGEO-powered document rewriting

Fetches a webpage and rewrites it based on AutoGEO content preference rules
to maximize visibility in LLM-generated answers.

Usage:
    python geo_rewrite.py <url> [--engine gemini|gpt|claude] [--dataset research|ecommerce]
    python geo_rewrite.py <url> --prompt-only  # Just output the rewrite prompt
    python geo_rewrite.py <url> -o output.md   # Rewrite and save to output.md
"""

import sys
import json
import os
import re
import argparse
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

# LLM calling capability
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: Anthropic SDK not found, LLM rewriting disabled")

# AutoGEO rules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from autogeo_rules import get_rules_for_audit, get_rules_key, AUTOGEO_RULES
    HAS_AUTOGEO_RULES = True
except ImportError:
    HAS_AUTOGEO_RULES = False
    print("Warning: AutoGEO rules not found, using basic rules")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_page_content(url: str, timeout: int = 30) -> tuple[str, str]:
    """
    Fetch and extract text content from a webpage.

    Returns:
        (title, text_content)
    """
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

        return title_text, text[:10000]  # Limit to 10k chars

    except Exception as e:
        return "", f"Error fetching page: {str(e)}"


def get_rewrite_prompt(
    content: str,
    url: str,
    business_type: str = "saas",
    engine: str = "gemini"
) -> str:
    """
    Generate an AutoGEO-style rewrite prompt.

    Args:
        content: Original document content
        url: Source URL
        business_type: Type of business (saas, ecommerce, etc.)
        engine: Target AI engine (gemini, gpt, claude)

    Returns:
        Rewrite prompt string
    """
    # Get rules based on business type and engine
    rules_key = get_rules_key(business_type, engine)
    rules = AUTOGEO_RULES.get(rules_key, AUTOGEO_RULES.get("research_gemini", []))

    rules_string = "- " + "\n- ".join(rules[:10])  # Use top 10 rules

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


def detect_business_type(title: str, content: str) -> str:
    """
    Simple heuristic to detect business type from content.

    Returns:
        "ecommerce", "saas", or "other"
    """
    text = (title + " " + content).lower()

    ecommerce_signals = [
        "price", "buy", "shop", "cart", "checkout", "product",
        "add to cart", "sale", "discount", "order", "payment"
    ]
    ecommerce_count = sum(1 for signal in ecommerce_signals if signal in text)

    if ecommerce_count >= 3:
        return "ecommerce"

    return "saas"


def call_llm_rewrite(prompt: str, engine: str = "gemini") -> str:
    """
    Call LLM to rewrite content using the provided prompt.

    Args:
        prompt: The rewrite prompt
        engine: Target AI engine (gemini, gpt, claude)

    Returns:
        Rewritten content from LLM
    """
    if not HAS_ANTHROPIC:
        return "[Error: Anthropic SDK not available]"

    try:
        client = Anthropic(
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic"),
            api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        )

        model = os.environ.get("ANTHROPIC_MODEL", "MiniMax-M2.7-highspeed")

        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract text from response, handling thinking blocks
        rewritten = ""
        for block in response.content:
            if hasattr(block, 'text'):
                rewritten += block.text
            # Skip thinking blocks

        return rewritten.strip()

    except Exception as e:
        return f"[Error calling LLM: {str(e)}]"


def rewrite_content(content: str, url: str, engine: str = "gemini") -> str:
    """
    Rewrite content using AutoGEO rules and LLM.

    Args:
        content: Original content
        url: Source URL
        engine: Target AI engine

    Returns:
        Rewritten content
    """
    business_type = detect_business_type("", content)
    prompt = get_rewrite_prompt(content, url, business_type, engine)

    if not HAS_ANTHROPIC:
        return prompt

    return call_llm_rewrite(prompt, engine)


def main():
    parser = argparse.ArgumentParser(description="GEO Rewrite - Rewrite webpage for AI visibility")
    parser.add_argument("url", help="URL of the page to rewrite")
    parser.add_argument("--engine", "-e", default="gemini",
                        choices=["gemini", "gpt", "claude"],
                        help="Target AI engine (default: gemini)")
    parser.add_argument("--dataset", "-d", default="research",
                        choices=["research", "ecommerce"],
                        help="Content type (default: research)")
    parser.add_argument("--prompt-only", "-p", action="store_true",
                        help="Only output the rewrite prompt, don't call LLM")
    parser.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    print(f"Fetching: {args.url}")
    title, content = fetch_page_content(args.url)

    if not content:
        print("Error: Could not fetch page content")
        sys.exit(1)

    print(f"Title: {title}")
    print(f"Content length: {len(content)} characters")

    # Detect business type
    business_type = detect_business_type(title, content)
    print(f"Detected business type: {business_type}")

    # Generate rewrite prompt
    prompt = get_rewrite_prompt(content, args.url, business_type, args.engine)

    if args.prompt_only:
        # Output just the prompt
        if args.output:
            with open(args.output, "w") as f:
                f.write(prompt)
            print(f"Prompt written to: {args.output}")
        else:
            print("\n" + "="*60)
            print(prompt)
            print("="*60)
    else:
        # Call LLM to rewrite
        print("\nCalling LLM to rewrite content...")
        rewritten = call_llm_rewrite(prompt, args.engine)

        if rewritten.startswith("[Error"):
            print(f"LLM Error: {rewritten}")
            print("\nFalling back to prompt-only mode")
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            sys.exit(1)

        print(f"\nRewritten content ({len(rewritten)} characters):")
        print("="*60)
        print(rewritten[:2000] + "..." if len(rewritten) > 2000 else rewritten)
        print("="*60)

        if args.output:
            with open(args.output, "w") as f:
                f.write(rewritten)
            print(f"\nRewritten content saved to: {args.output}")


if __name__ == "__main__":
    main()
