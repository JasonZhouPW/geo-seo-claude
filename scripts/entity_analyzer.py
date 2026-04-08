#!/usr/bin/env python3
"""
Entity Analyzer — Analyzes brand/person/product entities and knowledge graph readiness.
Supports three execution modes:
  - local:  Use Claude Code subagent for semantic analysis
  - api:    Use Anthropic SDK directly
  - auto:   Try local first, then api, finally regex fallback
"""

import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Literal, Optional

from bs4 import BeautifulSoup

# LLM support
try:
    from anthropic import Anthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Mode constants
LOCAL_MODE: Literal["local", "api", "auto"] = "local"
API_MODE: Literal["local", "api", "auto"] = "api"
AUTO_MODE: Literal["local", "api", "auto"] = "auto"


# ---------------------------------------------------------------------------
# Local mode: dispatch subagent within Claude Code environment
# ---------------------------------------------------------------------------


def _call_local_analysis(prompt: str, task_type: str = "entity_analysis") -> Optional[Dict]:
    """
    Dispatch a subagent for semantic analysis within Claude Code.
    Returns parsed JSON result or None if not available.
    """
    try:
        from agents.subagent_dispatcher import dispatch_semantic_agent

        result = dispatch_semantic_agent(prompt, task_type)
        if result:
            return json.loads(result)
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: try using subprocess to invoke Claude Code CLI
    try:
        import subprocess

        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = env.get("ANTHROPIC_AUTH_TOKEN", "")

        script = f'''
You are a semantic analysis agent. Analyze the following task and return ONLY valid JSON.

Task: {prompt}

Return JSON with your analysis results. JSON:
'''
        result = subprocess.run(
            ["claude", "-p", script, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# API mode: call Anthropic SDK directly
# ---------------------------------------------------------------------------


def _call_api(prompt: str, max_tokens: int = 2048) -> str:
    """Call LLM via Anthropic SDK."""
    if not HAS_ANTHROPIC:
        return ""

    try:
        client = Anthropic(
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic"),
            api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN", ""),
        )
        model = os.environ.get("ANTHROPIC_MODEL", "MiniMax-M2.7-highspeed")
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        result = ""
        for block in response.content:
            if hasattr(block, "text"):
                result += block.text
        return result.strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Mode router
# ---------------------------------------------------------------------------


def _resolve_mode(preferred_mode: str) -> str:
    """Resolve mode to actual execution mode."""
    if preferred_mode != "auto":
        return preferred_mode

    # auto: try local first if in Claude Code environment
    if os.environ.get("CLAUDE_API_KEY") or os.environ.get("CLAUDE_SESSION_ID"):
        return "local"
    if HAS_ANTHROPIC:
        return "api"
    return "regex"


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _entity_extraction_prompt(text: str) -> str:
    truncated = text[:8000]
    return (
        "Extract named entities from the following text. "
        "Return a JSON array with fields: text, label (PERSON/ORG/PRODUCT/LOCATION/EVENT), start.\n\n"
        f'Text: "{truncated}"\n\n'
        'Return ONLY valid JSON like: '
        '[{"text":"Google","label":"ORG","start":0},{"text":"Sundar Pichai","label":"PERSON","start":10}]\n\n'
        "If no entities found, return: []\n\n"
        "JSON:"
    )


def _relationship_extraction_prompt(text: str, brand_name: str) -> str:
    truncated = text[:6000]
    return (
        "Analyze the following text and extract named entities and knowledge triples.\n"
        "1. Named entities: text, label (PERSON/ORG/PRODUCT/LOCATION), start position\n"
        "2. Knowledge triples: subject, predicate, object for factual relationships\n"
        "Predicates: is_a, competitor, founded_by, used_by, part_of, acquired_by, rival_of, partner_of.\n\n"
        f'Text: "{truncated}"\n\n'
        'Return JSON like:\n'
        '{"entities": [{"text":"Google","label":"ORG","start":0}], '
        '"triples": [{"subject":"Google","predicate":"founded_by","object":"Larry Page"}]}\n\n'
        "If no triples, use empty arrays. Return ONLY the JSON object.\n\n"
        "JSON:"
    )


# ---------------------------------------------------------------------------
# Core extraction functions
# ---------------------------------------------------------------------------


def extract_named_entities(
    text: str,
    mode: Literal["local", "api", "auto"] = "auto",
) -> List[Dict]:
    """Extract named entities using specified mode."""
    resolved = _resolve_mode(mode)

    if resolved == "local":
        result = _call_local_analysis(
            _entity_extraction_prompt(text), task_type="entity_extraction"
        )
        if result and isinstance(result, list):
            return [
                {"text": str(e["text"]), "label": str(e["label"]).upper(), "start": int(e.get("start", 0))}
                for e in result
                if isinstance(e, dict) and "text" in e and "label" in e
            ]

    if resolved == "api":
        raw = _call_api(_entity_extraction_prompt(text))
        if raw:
            try:
                start_idx = raw.find("[")
                end_idx = raw.rfind("]") + 1
                if start_idx != -1 and end_idx > start_idx:
                    entities = json.loads(raw[start_idx:end_idx])
                    return [
                        {"text": str(e["text"]), "label": str(e["label"]).upper(), "start": int(e.get("start", 0))}
                        for e in entities
                        if isinstance(e, dict) and "text" in e and "label" in e
                    ]
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    return _extract_entities_regex(text)


def analyze_entity_relationships(
    soup: BeautifulSoup,
    brand_name: str,
    mode: Literal["local", "api", "auto"] = "auto",
) -> Dict:
    """Analyze entity relationships using specified mode."""
    text = soup.get_text(separator=" ", strip=True)
    resolved = _resolve_mode(mode)

    if resolved == "local":
        result = _call_local_analysis(
            _relationship_extraction_prompt(text, brand_name), task_type="relationship_extraction"
        )
        if result and isinstance(result, dict):
            return _build_relationship_result(result, text, brand_name)

    if resolved == "api":
        raw = _call_api(_relationship_extraction_prompt(text, brand_name))
        if raw:
            try:
                start_idx = raw.find("{")
                end_idx = raw.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    data = json.loads(raw[start_idx:end_idx])
                    return _build_relationship_result(data, text, brand_name)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    return _analyze_relationships_regex(text, brand_name)


def _build_relationship_result(data: Dict, text: str, brand_name: str) -> Dict:
    """Build standard result dict from LLM response data."""
    entities = [
        {"text": str(e["text"]), "label": str(e["label"]).upper(), "start": int(e.get("start", 0))}
        for e in data.get("entities", [])
        if isinstance(e, dict) and "text" in e and "label" in e
    ]

    triples = [
        {"subject": str(t["subject"]), "predicate": str(t["predicate"]), "object": str(t["object"])}
        for t in data.get("triples", [])
        if isinstance(t, dict) and "subject" in t and "predicate" in t and "object" in t
    ]

    unique_entities = set(e["text"] for e in entities)
    diversity_score = min(100, len(unique_entities) * 5)
    rel_density = min(100, len(triples) * 10)

    return {
        "total_entities_found": len(entities),
        "unique_entities": len(unique_entities),
        "entity_diversity_score": round(diversity_score, 1),
        "entity_types": dict(_count_by_type(entities)),
        "knowledge_triples": triples[:20],
        "triple_count": len(triples),
        "relationship_density_score": round(rel_density, 1),
        "brand_cooccurrence": _analyze_brand_cooccurrence(text, brand_name),
    }


# ---------------------------------------------------------------------------
# Regex fallback
# ---------------------------------------------------------------------------


def _extract_entities_regex(text: str) -> List[Dict]:
    """Fallback regex-based entity extraction."""
    entities = []

    org_patterns = [
        r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s+(?:Inc|LLC|Corp|Ltd|Group|Company)\.)\s*(?=\s|$|[.,;:!?])",
    ]
    for pattern in org_patterns:
        for match in re.finditer(pattern, text):
            entities.append({
                "text": match.group(1).strip(),
                "label": "ORG",
                "start": match.start(),
            })

    person_patterns = [
        r"\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+(?:Jr\.|Sr\.|III?|IV)\.?)?)\b",
        r"\b(?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
    ]
    for pattern in person_patterns:
        for match in re.finditer(pattern, text):
            entities.append({
                "text": match.group(0),
                "label": "PERSON",
                "start": match.start(),
            })

    return entities


def _analyze_relationships_regex(text: str, brand_name: str) -> Dict:
    """Fallback regex-based relationship extraction."""
    entities = _extract_entities_regex(text)

    relationship_patterns = [
        (r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:is|was|are|were)\s+a\s+([a-z][a-z]*(?:\s+[a-z]+)*)",
         "is_a"),
        (r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+vs\.?\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)",
         "competitor"),
        (r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:founded|created|built)\s+by\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)",
         "founded_by"),
        (r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:used|deployed)\s+(?:by|at|in)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)",
         "used_by"),
    ]

    triples = []
    for pattern, rel_type in relationship_patterns:
        for match in re.finditer(pattern, text):
            subject = match.group(1).strip()
            obj = match.group(2).strip()
            if len(subject) > 2 and len(obj) > 2:
                triples.append({
                    "subject": subject,
                    "predicate": rel_type,
                    "object": obj,
                })

    unique_entities = set(e["text"] for e in entities)
    diversity_score = min(100, len(unique_entities) * 5)
    rel_density = min(100, len(triples) * 10)

    return {
        "total_entities_found": len(entities),
        "unique_entities": len(unique_entities),
        "entity_diversity_score": round(diversity_score, 1),
        "entity_types": dict(_count_by_type(entities)),
        "knowledge_triples": triples[:20],
        "triple_count": len(triples),
        "relationship_density_score": round(rel_density, 1),
        "brand_cooccurrence": _analyze_brand_cooccurrence(text, brand_name),
    }


def _count_by_type(entities: List[Dict]) -> Dict[str, int]:
    counts = defaultdict(int)
    for e in entities:
        counts[e["label"]] += 1
    return dict(counts)


def _analyze_brand_cooccurrence(text: str, brand_name: str) -> Dict:
    """Check how often brand appears with industry terms."""
    industry_terms = [
        "SEO", "GEO", "AI", "machine learning", "analytics",
        "content marketing", "digital marketing", "search", "ranking",
        "visibility", "optimization", "traffic", "conversion",
    ]

    coocurring = {}
    text_lower = text.lower()

    for term in industry_terms:
        pattern = re.escape(term)
        matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
        if matches:
            coocurring[term] = len(matches)

    return {
        "industry_terms_found": len(coocurring),
        "cooccurrence_counts": coocurring,
    }


def analyze_internal_duplicates(soup: BeautifulSoup) -> Dict:
    """Detect internal content duplication using sentence similarity."""
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 100]
    if len(paragraphs) < 2:
        return {"duplicate_score": 100, "duplicates_found": []}

    duplicates = []
    for i in range(len(paragraphs)):
        for j in range(i + 1, len(paragraphs)):
            words_i = set(paragraphs[i].lower().split())
            words_j = set(paragraphs[j].lower().split())
            if not words_i or not words_j:
                continue
            overlap = len(words_i & words_j) / len(words_i | words_j)
            if overlap > 0.7:
                duplicates.append({
                    "para_i": i,
                    "para_j": j,
                    "overlap_ratio": round(overlap, 2),
                    "preview_i": paragraphs[i][:100],
                    "preview_j": paragraphs[j][:100],
                })

    dup_count = len(duplicates)
    dup_score = max(0, 100 - dup_count * 10)

    return {
        "duplicate_score": round(dup_score, 1),
        "duplicates_found": duplicates[:10],
        "total_checked": len(paragraphs),
    }


def compute_entity_graph_score(entity_rel: Dict, brand_cooc: Dict) -> Dict:
    """Compute overall entity knowledge graph readiness score."""
    diversity = entity_rel.get("entity_diversity_score", 0)
    relationship = entity_rel.get("relationship_density_score", 0)
    coocurring = brand_cooc.get("industry_terms_found", 0)

    score = diversity * 0.35 + relationship * 0.40 + min(100, coocurring * 10) * 0.25

    return {
        "entity_graph_score": round(score, 1),
        "breakdown": {
            "entity_diversity": diversity,
            "relationship_density": relationship,
            "brand_industry_coverage": round(min(100, coocurring * 10), 1),
        },
    }


def _entity_recommendations(entity_rel: Dict, dup: Dict) -> List[str]:
    recs = []
    if entity_rel.get("entity_diversity_score", 0) < 40:
        recs.append("Expand entity diversity — mention more products, people, and organizations")
    if entity_rel.get("relationship_density_score", 0) < 30:
        recs.append("Add more entity relationships (competitor comparisons, use cases, founder stories)")
    if dup.get("duplicate_score", 100) < 70:
        dup_count = len(dup.get("duplicates_found", []))
        recs.append(f"Reduce internal duplication — found {dup_count} near-duplicate paragraphs")
    return recs


if __name__ == "__main__":
    import argparse
    import json as json_mod

    parser = argparse.ArgumentParser(description="Entity Analyzer — Entity + relationship analysis")
    parser.add_argument("url", help="URL to analyze")
    parser.add_argument("brand", nargs="?", default="YourBrand", help="Brand name")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["local", "api", "auto"],
        default="auto",
        help="Execution mode: local (subagent), api (SDK), auto (try local then api)",
    )
    args = parser.parse_args()

    import requests

    resp = requests.get(args.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    soup = BeautifulSoup(resp.text, "lxml")

    entity_rel = analyze_entity_relationships(soup, args.brand, mode=args.mode)
    brand_cooc = entity_rel.get("brand_cooccurrence", {})
    dup = analyze_internal_duplicates(soup)
    graph_score = compute_entity_graph_score(entity_rel, brand_cooc)

    result = {
        **graph_score,
        "entity_analysis": entity_rel,
        "internal_duplicate_analysis": dup,
        "recommendations": _entity_recommendations(entity_rel, dup),
        "execution_mode": _resolve_mode(args.mode),
    }
    print(json_mod.dumps(result, indent=2, ensure_ascii=False))
