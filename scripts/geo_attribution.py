#!/usr/bin/env python3
"""
GEO Attribution — Estimates commercial value of GEO performance.
"""

import sys
from typing import Dict


def estimate_geo_attributed_traffic(
    citation_count: int,
    avg_ctr_from_ai_citation: float = 0.08,
    ai_visibility_monthly: int = 10000,
) -> Dict:
    """Estimate traffic from AI citations."""
    top_position = citation_count * 0.15
    secondary = citation_count * 0.05

    estimated_clicks = int((top_position + secondary) * avg_ctr_from_ai_citation * ai_visibility_monthly)

    return {
        "estimated_monthly_clicks": estimated_clicks,
        "citation_count": citation_count,
        "avg_ctr": avg_ctr_from_ai_citation,
        "confidence": "medium",
        "methodology": "citation_count * avg_ctr * visibility * position_weight",
    }


def estimate_geu_influenced_conversions(
    geo_traffic: int,
    base_conversion_rate: float = 0.025,
    geo_influence_factor: float = 1.4,
) -> Dict:
    """Estimate conversions influenced by GEO."""
    direct_conversions = int(geo_traffic * base_conversion_rate)
    influenced_conversions = int(geo_traffic * base_conversion_rate * geo_influence_factor)

    return {
        "direct_conversions": direct_conversions,
        "geo_influenced_conversions": influenced_conversions,
        "geo_influence_multiplier": geo_influence_factor,
        "attribution_note": "AI citations signal authority — influenced rate includes direct + halo effect",
    }


def project_geo_roi(
    monthly_investment: float,
    citation_count: int,
    avg_order_value: float = 100,
    conversion_rate: float = 0.025,
) -> Dict:
    """Project ROI from GEO investment."""
    traffic_est = estimate_geo_attributed_traffic(citation_count)
    clicks = traffic_est["estimated_monthly_clicks"]
    conversions = int(clicks * conversion_rate)
    revenue = conversions * avg_order_value
    cost = monthly_investment

    roi = ((revenue - cost) / cost * 100) if cost > 0 else 0

    return {
        "monthly_investment": monthly_investment,
        "estimated_monthly_clicks": clicks,
        "estimated_conversions": conversions,
        "estimated_revenue": round(revenue, 2),
        "roi_percentage": round(roi, 1),
        "roi_multiplier": round(revenue / cost, 2) if cost > 0 else 0,
        "payback_months": round(cost / (revenue / 12), 1) if revenue > 0 else None,
    }


def generate_attribution_report(
    geo_scores: Dict,
    citation_count: int,
    monthly_investment: float,
    avg_order_value: float = 100,
) -> Dict:
    """Generate full GEO attribution report."""
    traffic = estimate_geo_attributed_traffic(citation_count)
    conversions = estimate_geu_influenced_conversions(traffic["estimated_monthly_clicks"])
    roi = project_geo_roi(monthly_investment, citation_count, avg_order_value)

    return {
        "traffic_attribution": traffic,
        "conversion_attribution": conversions,
        "roi_projection": roi,
        "key_insight": _generate_insight(traffic, conversions, roi),
    }


def _generate_insight(traffic: Dict, conversions: Dict, roi: Dict) -> str:
    if roi["roi_multiplier"] > 3:
        return f"Strong GEO ROI — ${roi['estimated_revenue']:.0f} revenue from ${roi['monthly_investment']:.0f} investment"
    elif roi["roi_multiplier"] > 1:
        return f"Positive GEO ROI — each ${roi['monthly_investment']:.0f} generates ${roi['estimated_revenue']:.0f}"
    else:
        return "GEO investment requires optimization — current citations insufficient for positive ROI"


if __name__ == "__main__":
    import json
    if len(sys.argv) < 3:
        print("Usage: python geo_attribution.py <citation_count> <monthly_investment>")
        sys.exit(1)

    citations = int(sys.argv[1])
    investment = float(sys.argv[2])

    result = generate_attribution_report({}, citations, investment)
    print(json.dumps(result, indent=2))