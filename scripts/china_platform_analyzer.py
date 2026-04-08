#!/usr/bin/env python3
"""
China Platform Analyzer — Analyzes content readiness for Chinese AI platforms.
"""

import sys
import re
from typing import Dict, List
from bs4 import BeautifulSoup


CHINA_PLATFORMS = {
    "baidu_wenxin": {
        "name": "百度文心一言",
        "prefers": ["Baidu Schema", "Chinese content", "Structured data"],
    },
    "alibaba_tongyi": {
        "name": "通义千问",
        "prefers": ["Chinese language", "Alibaba ecosystem references", "E-commerce schemas"],
    },
    "bytedance_douai": {
        "name": "字节豆包",
        "prefers": ["Short video context", "ByteDance ecosystem", "Entertainment content"],
    },
}


def analyze_china_platform_readiness(html_content: str) -> Dict:
    """Analyze content readiness for Chinese AI platforms."""
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=" ", strip=True)

    chinese_char_ratio = _get_chinese_char_ratio(text)
    is_bilingual = 0.1 < chinese_char_ratio < 0.9

    schemas = _extract_schemas(soup)
    has_baidu_schema = any("Baidu" in s or "baidu" in s for s in schemas)
    has_ecommerce_schema = any("Product" in s or "Offer" in s for s in schemas)

    baidu_score = _compute_baidu_score(chinese_char_ratio, has_baidu_schema, soup)
    tongyi_score = _compute_tongyi_score(chinese_char_ratio, has_ecommerce_schema, soup)
    douai_score = _compute_douai_score(soup, text)

    return {
        "baidu_wenxin_score": baidu_score,
        "alibaba_tongyi_score": tongyi_score,
        "bytedance_douai_score": douai_score,
        "composite_china_score": round((baidu_score + tongyi_score + douai_score) / 3, 1),
        "chinese_char_ratio": round(chinese_char_ratio * 100, 1),
        "is_bilingual": is_bilingual,
        "schemas_found": schemas[:10],
        "recommendations": _china_recommendations(chinese_char_ratio, baidu_score, tongyi_score, douai_score),
    }


def _get_chinese_char_ratio(text: str) -> float:
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total_chars = len(text)
    return chinese_chars / total_chars if total_chars > 0 else 0


def _extract_schemas(soup: BeautifulSoup) -> List[str]:
    schemas = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string or "{}")
            if isinstance(data, dict):
                schemas.append(data.get("@type", ""))
        except:
            pass
    return schemas


def _compute_baidu_score(chinese_ratio: float, has_baidu_schema: bool, soup: BeautifulSoup) -> float:
    score = 0
    score += chinese_ratio * 40
    if has_baidu_schema:
        score += 30
    schema_count = len(soup.find_all("script", type="application/ld+json"))
    score += min(30, schema_count * 10)
    return round(min(100, score), 1)


def _compute_tongyi_score(chinese_ratio: float, has_ecommerce_schema: bool, soup: BeautifulSoup) -> float:
    score = 0
    score += chinese_ratio * 35
    if has_ecommerce_schema:
        score += 30
    alibaba_refs = 0
    page_text = soup.get_text()
    for term in ["淘宝", "天猫", "阿里巴巴", "支付宝"]:
        alibaba_refs += len(re.findall(term, page_text))
    score += min(20, alibaba_refs * 5)
    score += (1 - chinese_ratio) * 15 if chinese_ratio < 0.5 else 0
    return round(min(100, score), 1)


def _compute_douai_score(soup: BeautifulSoup, text: str) -> float:
    score = 50
    videos = soup.find_all(["video", "iframe"])
    score += min(30, len(videos) * 15)
    paragraphs = soup.find_all("p")
    avg_para_len = sum(len(p.get_text()) for p in paragraphs) / max(1, len(paragraphs)) if paragraphs else 0
    if avg_para_len < 200:
        score += 20
    return round(min(100, score), 1)


def _china_recommendations(chinese_ratio: float, baidu: float, tongyi: float, douai: float) -> List[str]:
    recs = []
    if chinese_ratio < 0.3:
        recs.append("Increase Chinese language content ratio for Baidu/Tongyi optimization")
    if baidu < 60:
        recs.append("Add Baidu-specific structured data (BaiduOrganization, BaiduProduct)")
    if tongyi < 60:
        recs.append("Consider e-commerce schema (Product, Offer) for Tongyi compatibility")
    if douai < 60:
        recs.append("Add more video content for DouAI/ByteDance ecosystem")
    return recs


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) > 1:
        import requests
        url = sys.argv[1]
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        result = analyze_china_platform_readiness(resp.text)
    else:
        result = {"error": "Usage: python china_platform_analyzer.py <url>"}
    print(json.dumps(result, indent=2, ensure_ascii=False))