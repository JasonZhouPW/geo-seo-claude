#!/usr/bin/env python3
"""
Competitive Analyzer — Compares GEO performance vs competitors.
"""

import sys
import re
import json
from typing import Dict, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def fetch_competitor_data(domain: str) -> Dict:
    """Fetch and analyze a competitor domain's public GEO signals."""
    try:
        resp = requests.get(
            f"https://{domain}",
            headers={"User-Agent": "Mozilla/5.0 AppleWebKit/537.36"},
            timeout=15,
        )
    except Exception:
        return {"error": f"Could not fetch {domain}"}

    soup = BeautifulSoup(resp.text, "lxml")

    return {
        "domain": domain,
        "fetched_at": datetime.now().isoformat(),
        "status": resp.status_code,
        "title": soup.find("title").get_text(strip=True) if soup.find("title") else None,
        "meta_description": (
            soup.find("meta", attrs={"name": "description"}).get("content", "")
            if soup.find("meta", attrs={"name": "description"})
            else ""
        ),
        "h1_count": len(soup.find_all("h1")),
        "h2_count": len(soup.find_all("h2")),
        "word_count": len(soup.get_text().split()),
        "internal_links": len(soup.find_all("a", href=re.compile(r"^/"))),
        "external_links": len(soup.find_all("a", href=re.compile(r"^https?://(?!.*" + re.escape(domain) + r")"))),
        "images_with_alt": len([img for img in soup.find_all("img") if img.get("alt")]),
        "schema_count": len(soup.find_all("script", type="application/ld+json")),
        "has_robots_txt": _check_robots_txt(domain),
        "has_sitemap": _check_sitemap(domain),
    }


def _check_robots_txt(domain: str) -> bool:
    try:
        resp = requests.get(f"https://{domain}/robots.txt", timeout=5)
        return resp.status_code == 200
    except:
        return False


def _check_sitemap(domain: str) -> bool:
    try:
        resp = requests.get(f"https://{domain}/sitemap.xml", timeout=5)
        return resp.status_code == 200
    except:
        return False


def compare_competitors(target_domain: str, competitor_domains: List[str]) -> Dict:
    """Compare target domain against competitors across GEO signals."""
    competitors = [target_domain] + competitor_domains
    results = {}

    for domain in competitors:
        results[domain] = fetch_competitor_data(domain)

    comparison = {"domains": {}}

    for domain, data in results.items():
        if "error" not in data:
            comparison["domains"][domain] = {
                "word_count": data["word_count"],
                "heading_depth": data["h1_count"] + data["h2_count"],
                "link_profile_score": data["internal_links"] + data["external_links"],
                "image_optimization": data["images_with_alt"],
                "schema_implementation": data["schema_count"],
                "technical_readiness": sum([
                    (data.get("has_robots_txt", False)) * 20,
                    (data.get("has_sitemap", False)) * 20,
                    min(30, data["h1_count"] * 15),
                    min(30, data["h2_count"] * 3),
                ]),
            }

    gaps = {}
    target = comparison["domains"].get(target_domain, {})

    for domain, metrics_data in comparison["domains"].items():
        if domain == target_domain:
            continue
        gap_scores = {}
        for metric, value in metrics_data.items():
            target_val = target.get(metric, 0)
            gap_scores[metric] = {
                "target": target_val,
                "competitor": value,
                "gap": target_val - value,
                "gap_pct": round((target_val - value) / max(target_val, 1) * 100, 1),
            }
        gaps[domain] = gap_scores

    sov_scores = {}
    for domain, m in comparison["domains"].items():
        score = (
            m["word_count"] / 100 * 0.3 +
            m["link_profile_score"] / 10 * 0.3 +
            m["schema_implementation"] * 2 * 0.2 +
            m["technical_readiness"] * 0.2
        )
        sov_scores[domain] = round(score, 1)

    return {
        "target_domain": target_domain,
        "competitors": competitor_domains,
        "raw_data": results,
        "metrics_comparison": comparison,
        "share_of_voice": sov_scores,
        "competitive_gaps": gaps,
        "recommendations": _competitive_recommendations(target, gaps),
    }


def _competitive_recommendations(target: Dict, gaps: Dict) -> List[str]:
    recs = []
    if not target:
        return ["Unable to analyze — check domain accessibility"]

    for comp_domain, gap_scores in gaps.items():
        for metric, gap_data in gap_scores.items():
            if gap_data["gap"] < -20:
                recs.append(
                    f"vs {comp_domain}: {metric.replace('_', ' ').title()} "
                    f"({gap_data['target']} vs {gap_data['competitor']}) — "
                    f"target is {abs(gap_data['gap_pct'])}% behind"
                )
    return recs[:10]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python competitive_analyzer.py <target_domain> <competitor1,competitor2,...>")
        sys.exit(1)

    target = sys.argv[1]
    competitors = [d.strip() for d in sys.argv[2].split(",")]

    result = compare_competitors(target, competitors)
    print(json.dumps(result, indent=2, ensure_ascii=False))