"""Centralized scoring logic for all GEO metrics.
All score calculations live here — SKILL.md references this module.
Weights and formulas are documented and testable.
"""

from typing import List, Dict, Any, Optional


# === WEIGHTS (source of truth) ===
WEIGHTS = {
    "ai_citability": 0.25,
    "brand_authority": 0.20,
    "content_quality": 0.20,
    "technical": 0.15,
    "structured_data": 0.10,
    "platform_optimization": 0.10,
}


def compute_citability_score(passage_score: float, word_count: int,
                              has_statistics: bool, has_definitions: bool) -> float:
    """Compute normalized citability score 0-100."""
    base = passage_score * 0.4
    word_bonus = 20 if 134 <= word_count <= 167 else (10 if word_count > 100 else 0)
    stat_bonus = 15 if has_statistics else 0
    def_bonus = 10 if has_definitions else 0
    return min(100, base + word_bonus + stat_bonus + def_bonus)


def compute_eeat_score(experience: float, expertise: float,
                        authority: float, trustworthiness: float) -> float:
    """Compute E-E-A-T composite score 0-100."""
    return (experience * 0.1 + expertise * 0.3 +
            authority * 0.3 + trustworthiness * 0.3)


def compute_geu_dimension_scores(dimension_scores: List[Dict]) -> Dict[str, float]:
    """Aggregate GEU evaluation dimensions into sub-scores."""
    dimension_names = [d["dimension"] for d in dimension_scores]
    dimension_values = [d["score"] for d in dimension_scores]
    dimension_weights = [d.get("weight", 1.0) for d in dimension_scores]
    total_weight = sum(dimension_weights)
    weighted = sum(v * w for v, w in zip(dimension_values, dimension_weights))
    return {
        "geu_sub_scores": dict(zip(dimension_names, dimension_values)),
        "geu_composite": weighted / total_weight if total_weight else 0,
    }


def normalize_platform_scores(platform_scores: Dict[str, float]) -> Dict[str, float]:
    """Normalize platform-specific scores to 0-100 scale."""
    return {platform: min(100, max(0, score)) for platform, score in platform_scores.items()}


def compute_final_geu_score(citability: float, brand: float, content: float,
                              technical: float, structured: float,
                              platform: Dict[str, float],
                              geu_dimensions: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Compute the final weighted GEO score.

    Args:
        citability: AI citability score (0-100)
        brand: Brand authority score (0-100)
        content: Content quality score (0-100)
        technical: Technical SEO score (0-100)
        structured: Structured data score (0-100)
        platform: Dict of platform-specific scores
        geu_dimensions: Optional list of GEU dimension dicts

    Returns:
        Dict with composite score and breakdown
    """
    platform_avg = sum(platform.values()) / len(platform) if platform else 0

    raw = (
        WEIGHTS["ai_citability"] * citability +
        WEIGHTS["brand_authority"] * brand +
        WEIGHTS["content_quality"] * content +
        WEIGHTS["technical"] * technical +
        WEIGHTS["structured_data"] * structured +
        WEIGHTS["platform_optimization"] * platform_avg
    )

    result = {
        "composite_score": round(raw, 1),
        "weights": WEIGHTS,
        "breakdown": {
            "ai_citability": round(citability, 1),
            "brand_authority": round(brand, 1),
            "content_quality": round(content, 1),
            "technical": round(technical, 1),
            "structured_data": round(structured, 1),
            "platform_optimization": round(platform_avg, 1),
        },
    }

    if geu_dimensions:
        dimension_result = compute_geu_dimension_scores(geu_dimensions)
        result["geu_composite"] = round(dimension_result["geu_composite"], 1)
        result["geu_sub_scores"] = dimension_result["geu_sub_scores"]

    return result
