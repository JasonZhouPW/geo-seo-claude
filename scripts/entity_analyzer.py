#!/usr/bin/env python3
"""
Entity Analyzer — Analyzes brand/person/product entities and knowledge graph readiness.
"""

import sys
import re
from typing import Dict, List, Set
from collections import defaultdict
from bs4 import BeautifulSoup


def extract_named_entities(text: str) -> List[Dict]:
    """Extract named entities from text using pattern matching."""
    entities = []

    # Check org patterns first to avoid org names like "Google Inc." being
    # incorrectly matched as person names by the title pattern.
    org_patterns = [
        r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Inc\.|LLC|Corp\.|Ltd\.|Group|Company)(?=\s|$|[.,;:!?]))",
    ]
    for pattern in org_patterns:
        for match in re.finditer(pattern, text):
            entities.append({
                "text": match.group(0),
                "label": "ORG",
                "start": match.start(),
            })

    person_patterns = [
        r"\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+(?:Jr\.|Sr\.|III?|IV)\.?)?)\b",
        r"\b(Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
    ]
    for pattern in person_patterns:
        for match in re.finditer(pattern, text):
            entities.append({
                "text": match.group(0),
                "label": "PERSON",
                "start": match.start(),
            })

    return entities


def analyze_entity_relationships(soup: BeautifulSoup, brand_name: str) -> Dict:
    """Analyze entity relationships and knowledge triple coverage."""
    text = soup.get_text(separator=" ", strip=True)
    entities = extract_named_entities(text)

    relationship_patterns = [
        (r"([A-Z][a-zA-Z](?:\s+[A-Z][a-zA-Z]+)*)\s+(?:is|was|are|were|becomes?)\s+([a-z][a-z]+(?:\s+[a-z]+)*)",
         "is_a"),
        (r"([A-Z][a-zA-Z](?:\s+[A-Z][a-zA-Z]+)*)\s+vs\.?\s+([A-Z][a-zA-Z](?:\s+[A-Z][a-zA-Z]+)*)",
         "competitor"),
        (r"([A-Z][a-zA-Z](?:\s+[A-Z][a-zA-Z]+)*)\s+(?:founded|created|built)\s+(?:by|with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
         "founded_by"),
        (r"([A-Z][a-zA-Z](?:\s+[A-Z][a-zA-Z]+)*)\s+(?:used|adopted|deployed)\s+(?:by|at|in)\s+([A-Z][a-zA-Z](?:\s+[A-Z][a-zA-Z]+)*)",
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


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python entity_analyzer.py <url> [brand_name]")
        sys.exit(1)

    url = sys.argv[1]
    brand = sys.argv[2] if len(sys.argv) > 2 else "YourBrand"

    import requests
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    soup = BeautifulSoup(resp.text, "lxml")

    entity_rel = analyze_entity_relationships(soup, brand)
    brand_cooc = entity_rel.get("brand_cooccurrence", {})
    dup = analyze_internal_duplicates(soup)
    graph_score = compute_entity_graph_score(entity_rel, brand_cooc)

    result = {
        **graph_score,
        "entity_analysis": entity_rel,
        "internal_duplicate_analysis": dup,
        "recommendations": _entity_recommendations(entity_rel, dup),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _entity_recommendations(entity_rel: Dict, dup: Dict) -> List[str]:
    recs = []
    if entity_rel.get("entity_diversity_score", 0) < 40:
        recs.append("Expand entity diversity — mention more products, people, and organizations")
    if entity_rel.get("relationship_density_score", 0) < 30:
        recs.append("Add more entity relationships (competitor comparisons, use cases, founder stories)")
    if dup.get("duplicate_score", 100) < 70:
        recs.append(f"Reduce internal duplication — found {len(dup.get('duplicates_found', []))} near-duplicate paragraphs")
    return recs
