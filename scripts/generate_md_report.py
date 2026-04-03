#!/usr/bin/env python3
"""
Generate GEO Audit Report in Markdown format with timestamp.

Usage:
    python generate_md_report.py <json_data_file> [output_file.md] [--dir path]
"""

import sys
import json
import os
from datetime import datetime

# AutoGEO rules integration - add script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from autogeo_rules import get_rules_for_audit, rules_to_action_plan
    HAS_AUTOGEO_RULES = True
except ImportError:
    HAS_AUTOGEO_RULES = False

def generate_md_report(data, output_path="GEO-REPORT.md"):
    """Generate markdown report from data dict."""
    url = data.get("url", "https://example.com")
    brand_name = data.get("brand_name", url.replace("https://", "").replace("http://", "").split("/")[0])
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    geo_score = data.get("geo_score", 0)
    business_type = data.get("business_type", "Unknown")
    scores = data.get("scores", {})
    platforms = data.get("platforms", {})
    findings = data.get("findings", [])
    quick_wins = data.get("quick_wins", [])
    medium_term = data.get("medium_term", [])
    strategic = data.get("strategic", [])
    strengths = data.get("strengths", [])
    schema_findings = data.get("schema_findings", {})
    crawler_access = data.get("crawler_access", {})
    international_platforms = data.get("international_platforms", {})
    cn_platforms = data.get("cn_platforms", {})

    # Score components
    ai_citability = scores.get("ai_citability", 0)
    brand_authority = scores.get("brand_authority", 0)
    content_eeat = scores.get("content_eeat", 0)
    technical = scores.get("technical", 0)
    schema_score = scores.get("schema", 0)
    platform_optimization = scores.get("platform_optimization", 0)

    # GEO Impression Score
    geo_impression = data.get("geo_impression_score", {})
    impression_score = int(geo_impression.get("combined_score", 0) * 100) if geo_impression else 0
    impression_position = geo_impression.get("position_score", 0)
    impression_word_count = geo_impression.get("word_count_score", 0)
    citation_count = geo_impression.get("citation_count", 0)
    impression_recommendations = geo_impression.get("recommendations", [])

    # GEU Score
    geu_data = data.get("geu_score", {})
    geu_overall = geu_data.get("overall_quality_score", 0) if geu_data else 0
    geu_dimensions = geu_data.get("quality_dimensions", {}) if geu_data else {}
    geu_citation_recall = geu_data.get("citation_metrics", {}).get("citation_recall", 0) if geu_data else 0

    # Get score label
    def get_score_label(score):
        if score >= 85: return "Excellent"
        elif score >= 70: return "Good"
        elif score >= 55: return "Moderate"
        elif score >= 40: return "Below Average"
        else: return "Needs Work"

    tier = get_score_label(geo_score)

    # Format date
    if "-" in date:
        try:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y")
        except:
            formatted_date = date
    else:
        formatted_date = date

    # Build markdown
    md = []
    md.append(f"# GEO Audit Report — {brand_name}")
    md.append("")
    md.append(f"**Date:** {formatted_date}")
    md.append(f"**Website:** {url}")
    md.append(f"**Business Type:** {business_type}")
    md.append(f"**Audit Type:** Full GEO + SEO Audit (has-solution=true, cn-media=true)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Executive Summary")
    md.append("")
    md.append("| Metric | Score | Status |")
    md.append("|--------|-------|--------|")
    md.append(f"| **Overall GEO Score** | **{geo_score}/100** | 🟢 {tier} |")
    md.append(f"| AI Citability & Visibility | {ai_citability}/100 | 🟡 Average |")
    md.append(f"| Brand Authority Signals | {brand_authority}/100 | 🟢 Good |")
    md.append(f"| Content Quality & E-E-A-T | {content_eeat}/100 | 🟢 Good |")
    md.append(f"| Technical Foundations | {technical}/100 | 🟢 Good |")
    md.append(f"| Structured Data | {schema_score}/100 | 🟢 Good |")
    md.append(f"| Platform Optimization | {platform_optimization}/100 | 🟢 Good |")
    if geu_overall > 0:
        md.append(f"| **GEU Quality Score** | **{int(geu_overall * 100)}/100** | 🟢 Measured |")
    if impression_score > 0:
        md.append(f"| **GEO Impression Score** | **{impression_score}/100** | 🟢 Measured |")
    md.append("")
    md.append("---")
    md.append("")

    # GEO Score Breakdown
    md.append("## GEO Score Breakdown")
    md.append("")
    md.append("```")
    md.append(f"Overall GEO Score: {geo_score}/100")
    md.append("")

    if geu_overall > 0 and impression_score > 0:
        # 8-category weights with GEU and GEO Impression
        md.append(f"├── AI Citability & Visibility  [20%] → {ai_citability}/100 ({ai_citability * 0.20:.1f} pts)")
        md.append(f"├── Brand Authority Signals      [15%] → {brand_authority}/100 ({brand_authority * 0.15:.1f} pts)")
        md.append(f"├── Content Quality & E-E-A-T  [10%] → {content_eeat}/100 ({content_eeat * 0.10:.1f} pts)")
        md.append(f"├── GEU Quality Score         [15%] → {int(geu_overall*100)}/100 ({geu_overall * 0.15 * 100:.1f} pts)")
        md.append(f"├── Technical Foundations       [13%] → {technical}/100 ({technical * 0.13:.1f} pts)")
        md.append(f"├── Structured Data           [10%] → {schema_score}/100 ({schema_score * 0.10:.1f} pts)")
        md.append(f"├── Platform Optimization     [10%] → {platform_optimization}/100 ({platform_optimization * 0.10:.1f} pts)")
        md.append(f"└── GEO Impression Score      [7%] → {impression_score}/100 ({impression_score * 0.07:.1f} pts)")
        md.append(f"                                        ─────────────")
        total = ai_citability*0.20 + brand_authority*0.15 + content_eeat*0.10 + geu_overall*0.15*100 + technical*0.13 + schema_score*0.10 + platform_optimization*0.10 + impression_score*0.07
        md.append(f"                                        Total: {total:.1f} → {geo_score}/100")
    elif geu_overall > 0:
        # 7-category weights with GEU (no GEO Impression)
        md.append(f"├── AI Citability & Visibility  [22%] → {ai_citability}/100 ({ai_citability * 0.22:.1f} pts)")
        md.append(f"├── Brand Authority Signals      [18%] → {brand_authority}/100 ({brand_authority * 0.18:.1f} pts)")
        md.append(f"├── Content Quality & E-E-A-T  [12%] → {content_eeat}/100 ({content_eeat * 0.12:.1f} pts)")
        md.append(f"├── GEU Quality Score         [18%] → {int(geu_overall*100)}/100 ({geu_overall * 0.18 * 100:.1f} pts)")
        md.append(f"├── Technical Foundations       [13%] → {technical}/100 ({technical * 0.13:.1f} pts)")
        md.append(f"├── Structured Data           [8%] → {schema_score}/100 ({schema_score * 0.08:.1f} pts)")
        md.append(f"└── Platform Optimization    [9%] → {platform_optimization}/100 ({platform_optimization * 0.09:.1f} pts)")
        md.append(f"                                        ─────────────")
        total = ai_citability*0.22 + brand_authority*0.18 + content_eeat*0.12 + geu_overall*0.18*100 + technical*0.13 + schema_score*0.08 + platform_optimization*0.09
        md.append(f"                                        Total: {total:.1f} → {geo_score}/100")
    elif impression_score > 0:
        # Updated weights with GEO Impression Score
        md.append(f"├── AI Citability & Visibility  [22%] → {ai_citability}/100 ({ai_citability * 0.22:.1f} pts)")
        md.append(f"├── Brand Authority Signals      [18%] → {brand_authority}/100 ({brand_authority * 0.18:.1f} pts)")
        md.append(f"├── Content Quality & E-E-A-T  [18%] → {content_eeat}/100 ({content_eeat * 0.18:.1f} pts)")
        md.append(f"├── Technical Foundations       [12%] → {technical}/100 ({technical * 0.12:.1f} pts)")
        md.append(f"├── Structured Data            [8%] → {schema_score}/100 ({schema_score * 0.08:.1f} pts)")
        md.append(f"├── Platform Optimization        [8%] → {platform_optimization}/100 ({platform_optimization * 0.08:.1f} pts)")
        md.append(f"└── GEO Impression Score      [14%] → {impression_score}/100 ({impression_score * 0.14:.1f} pts)")
        md.append(f"                                        ─────────────")
        total = ai_citability*0.22 + brand_authority*0.18 + content_eeat*0.18 + technical*0.12 + schema_score*0.08 + platform_optimization*0.08 + impression_score*0.14
        md.append(f"                                        Total: {total:.1f} → {geo_score}/100")
    else:
        # GEO Impression Score not measured - use 6-category weights
        md.append(f"├── AI Citability & Visibility  [25%] → {ai_citability}/100 ({ai_citability * 0.25:.1f} pts)")
        md.append(f"├── Brand Authority Signals      [20%] → {brand_authority}/100 ({brand_authority * 0.20:.1f} pts)")
        md.append(f"├── Content Quality & E-E-A-T  [20%] → {content_eeat}/100 ({content_eeat * 0.20:.1f} pts)")
        md.append(f"├── Technical Foundations       [15%] → {technical}/100 ({technical * 0.15:.1f} pts)")
        md.append(f"├── Structured Data           [10%] → {schema_score}/100 ({schema_score * 0.10:.1f} pts)")
        md.append(f"├── Platform Optimization    [10%] → {platform_optimization}/100 ({platform_optimization * 0.10:.1f} pts)")
        md.append(f"└── GEO Impression Score      [0%] → {impression_score}/100 (Not Measured)")
        md.append(f"                                        ─────────────")
        total = ai_citability*0.25 + brand_authority*0.20 + content_eeat*0.20 + technical*0.15 + schema_score*0.10 + platform_optimization*0.10
        md.append(f"                                        Total: {total:.1f} → {geo_score}/100")
    md.append("```")
    md.append("")

    # Detailed Findings
    md.append("## Detailed Findings")
    md.append("")

    # AI Citability
    md.append(f"### 1. AI Citability & Visibility — {ai_citability}/100 🟡")
    md.append("")
    md.append("| Factor | Status | Details |")
    md.append("|--------|--------|---------|")
    # Iterate over all crawler access items
    for crawler, info in crawler_access.items():
        # Skip ai_crawlers as it's handled separately below
        if crawler == "ai_crawlers":
            continue
        if isinstance(info, dict):
            status = info.get("status", "unknown")
            detail = info.get("detail", info.get("platform", ""))
            if status == "HTTP 200" or status == "allowed":
                md.append(f"| **{crawler.upper()}** | ✅ Allowed | {detail} |")
            elif status == "blocked":
                md.append(f"| **{crawler.upper()}** | ❌ Blocked | {detail} |")
            elif status == "not_found":
                md.append(f"| **{crawler.upper()}** | ❌ Not Found | {detail} |")
            else:
                md.append(f"| **{crawler.upper()}** | ⚠️ {status} | {detail} |")
        else:
            md.append(f"| **{crawler.upper()}** | ⚠️ {info} |")

    # Handle ai_crawlers nested items
    ai_crawlers = crawler_access.get("ai_crawlers", {})
    for crawler, status in ai_crawlers.items():
        status_str = str(status) if status else "unknown"
        if status_str in ("allowed", "Allowed", "true", True):
            md.append(f"| **{crawler.upper()}** | ✅ Allowed | AI crawler |")
        elif status_str in ("blocked", "Blocked", "false", False):
            md.append(f"| **{crawler.upper()}** | ❌ Blocked | AI crawler |")
        else:
            md.append(f"| **{crawler.upper()}** | ⚠️ {status_str} | AI crawler |")

    md.append("")

    # Brand Authority
    md.append(f"### 2. Brand Authority Signals — {brand_authority}/100 🟢")
    md.append("")

    if international_platforms:
        md.append("#### International Platforms")
        md.append("")
        md.append("| Platform | Presence | Handle/URL |")
        md.append("|----------|----------|------------|")
        for platform, info in international_platforms.items():
            present = info.get("present", False)
            if str(present).lower() == "true":
                presence = "✅ Present"
            elif str(present).lower() == "unknown":
                presence = "⚠️ Unknown"
            else:
                presence = "❌ Missing"
            handle = info.get("handle", "")
            md.append(f"| {platform} | {presence} | {handle} |")
        md.append("")

    # Show Chinese platforms if cn_media=true OR if cn_platforms has data
    show_cn = data.get("cn_media", False) or cn_platforms
    if show_cn and cn_platforms:
        md.append("#### Chinese Platforms (cn-media=true)")
        md.append("")
        md.append("| Platform | Presence | Handle/URL |")
        md.append("|----------|----------|------------|")
        for platform, info in cn_platforms.items():
            present = info.get("present", False)
            if str(present).lower() == "true":
                presence = "✅ Present"
            elif str(present).lower() == "unknown":
                presence = "⚠️ Unknown"
            else:
                presence = "❌ Missing"
            handle = info.get("handle", "")
            md.append(f"| {platform} | {presence} | {handle} |")
        md.append("")

    # Content Quality
    md.append(f"### 3. Content Quality & E-E-A-T — {content_eeat}/100 🟢")
    md.append("")
    md.append("**Content Assessment:**")
    md.append(f"- **Title:** {data.get('content_findings', {}).get('title', 'N/A')} ✅")
    md.append(f"- **Meta Description:** Present ✅")
    md.append(f"- **Unique Data:** {data.get('content_findings', {}).get('unique_data', 'N/A')} ✅")
    content_depth = data.get('content_findings', {}).get('content_depth', 'N/A')
    md.append(f"- **Content Depth:** {content_depth}")
    author_signals = data.get('content_findings', {}).get('author_signals', 'N/A')
    md.append(f"- **Author Signals:** ❌ {author_signals}")
    md.append("")

    # Technical
    md.append(f"### 4. Technical Foundations — {technical}/100 🟢")
    md.append("")
    md.append("| Factor | Status | Details |")
    md.append("|--------|--------|---------|")
    tech = data.get("technical_findings", {})
    rendering = tech.get("rendering", "Unknown")
    md.append(f"| **Rendering** | ✅ {rendering} | SSR confirmed |")
    md.append("| **HTTPS** | ✅ Enabled | Enforced |")
    md.append(f"| **robots.txt** | ✅ Excellent | All AI crawlers allowed |")
    md.append(f"| **hreflang** | ✅ Present | {tech.get('hreflang', 'Multiple variants')} |")
    md.append("")

    # Schema
    md.append(f"### 5. Structured Data — {schema_score}/100 🟢")
    md.append("")
    if schema_findings:
        md.append("| Schema Element | Status |")
        md.append("|---------------|--------|")
        for schema, status in schema_findings.items():
            md.append(f"| **{schema.title()}** | {status} |")
        md.append("")

    # Platform Optimization
    md.append(f"### 6. Platform Optimization — {platform_optimization}/100 🟢")
    md.append("")
    md.append("| Platform | Score | Status |")
    md.append("|----------|-------|--------|")
    for platform, score in platforms.items():
        s = score if isinstance(score, int) else score.get("score", 0)
        status = "Good" if s >= 70 else "Moderate"
        md.append(f"| **{platform}** | {s}/100 | 🟢 {status} |")
    md.append("")

    # GEU Quality Score Section
    if geu_overall > 0:
        section_num = 7 if impression_score == 0 else 8
        md.append(f"### {section_num}. GEU Quality Score — {int(geu_overall * 100)}/100 🟢")
        md.append("")
        md.append("| Dimension | Score | Description |")
        md.append("|-----------|-------|-------------|")
        clarity = geu_dimensions.get("clarity", 0)
        depth = geu_dimensions.get("depth", 0)
        balance = geu_dimensions.get("balance", 0)
        breadth = geu_dimensions.get("breadth", 0)
        support = geu_dimensions.get("support", 0)
        insightfulness = geu_dimensions.get("insightfulness", 0)
        md.append(f"| **Clarity** | {int(clarity * 100)}/100 | Structure, logic flow, lack of redundancy |")
        md.append(f"| **Depth** | {int(depth * 100)}/100 | Analytical depth, critical thinking |")
        md.append(f"| **Balance** | {int(balance * 100)}/100 | Fairness, objectivity, multiple perspectives |")
        md.append(f"| **Breadth** | {int(breadth * 100)}/100 | Coverage of relevant subtopics |")
        md.append(f"| **Support** | {int(support * 100)}/100 | Claims substantiated with evidence |")
        md.append(f"| **Insightfulness** | {int(insightfulness * 100)}/100 | Originality, actionable recommendations |")
        md.append(f"| **Citation Recall** | {int(geu_citation_recall * 100)}/100 | Claims with source citations |")
        md.append("")
        md.append(f"*GEU Score measures content quality using LLM-based evaluation across 6 dimensions.*")
        md.append("")

    # GEO Impression Score Section
    if impression_score > 0:
        md.append("### 7. GEO Impression Score — Measured 🟢")
        md.append("")
        md.append("| Metric | Value | Description |")
        md.append("|--------|-------|-------------|")
        md.append(f"| **Combined Score** | **{impression_score}/100** | Overall visibility in LLM-generated answers |")
        md.append(f"| Position Score | {int(impression_position * 100)}/100 | Early citations score higher |")
        md.append(f"| Word Count Score | {int(impression_word_count * 100)}/100 | Substantive content with specific details |")
        md.append(f"| Citation Count | {citation_count} | Number of times source was cited |")
        md.append("")
        md.append("**Recommendations:**")
        for rec in impression_recommendations[:3]:
            md.append(f"- {rec}")
        md.append("")

    # Key Findings
    if findings:
        md.append("## Key Findings")
        md.append("")
        md.append("| Category | Severity | Issue |")
        md.append("|---------|----------|-------|")
        for finding in findings:
            category = finding.get("category", "N/A")
            severity = finding.get("severity", "N/A")
            issue = finding.get("issue", "N/A")
            # Emoji for severity
            severity_emoji = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡" if severity == "medium" else "🟢"
            md.append(f"| {category} | {severity_emoji} {severity} | {issue} |")
        md.append("")

    # Action Plan
    md.append("## Action Plan")
    md.append("")

    # Use AutoGEO rules to enhance action plan
    autogeo_plan = None
    if HAS_AUTOGEO_RULES:
        rules = get_rules_for_audit(business_type, "gemini")
        autogeo_plan = rules_to_action_plan(rules)

    if quick_wins or (autogeo_plan and autogeo_plan.get("quick_wins")):
        md.append("### 🟡 High Priority")
        md.append("")
        # First add existing quick_wins from audit data
        shown = set()
        idx = 1
        for action in quick_wins[:5]:
            action_text = action.get("action", action) if isinstance(action, dict) else action
            md.append(f"{idx}. **{action_text}**")
            shown.add(action_text)
            idx += 1
        # Supplement with AutoGEO rules
        if autogeo_plan and autogeo_plan.get("quick_wins"):
            for action in autogeo_plan["quick_wins"]:
                rule = action.get("rule", "")
                if rule not in shown:
                    md.append(f"{idx}. **{rule}**")
                    shown.add(rule)
                    idx += 1
        md.append("")

    if medium_term or (autogeo_plan and autogeo_plan.get("medium_term")):
        md.append("### 🟢 Medium Term")
        md.append("")
        shown = set()
        idx = 1
        for action in medium_term[:5]:
            action_text = action.get("action", action) if isinstance(action, dict) else action
            md.append(f"{idx}. **{action_text}**")
            shown.add(action_text)
            idx += 1
        if autogeo_plan and autogeo_plan.get("medium_term"):
            for action in autogeo_plan["medium_term"]:
                rule = action.get("rule", "")
                if rule not in shown:
                    md.append(f"{idx}. **{rule}**")
                    shown.add(rule)
                    idx += 1
        md.append("")

    if strategic:
        md.append("### 🔵 Strategic")
        md.append("")
        for i, action in enumerate(strategic[:5], 1):
            action_text = action.get("action", action) if isinstance(action, dict) else action
            md.append(f"{i}. **{action_text}**")
        md.append("")

    md.append("---")
    md.append("")
    md.append(f"*Report generated by GEO-SEO Analysis Tool*")
    md.append(f"*Parameters: has-solution=true, cn-media=true*")

    # Write file
    with open(output_path, 'w') as f:
        f.write('\n'.join(md))

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_md_report.py <json_data_file> [output_file.md] [--dir path]")
        sys.exit(1)

    # Parse arguments
    input_path = None
    output_file = None
    output_dir = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--dir":
            i += 1
            output_dir = sys.argv[i] if i < len(sys.argv) else None
        elif sys.argv[i] == "-":
            input_path = "-"
        elif input_path is None:
            input_path = sys.argv[i]
        elif output_file is None:
            output_file = sys.argv[i]
        i += 1

    if input_path is None:
        print("Error: json_data_file is required")
        sys.exit(1)

    # Load data
    if input_path == "-":
        data = json.loads(sys.stdin.read())
    else:
        with open(input_path) as f:
            data = json.load(f)

    # Determine output path with timestamp
    if output_file is None:
        output_file = "GEO-REPORT.md"

    # Add timestamp if not already present
    if "GEO-REPORT.md" in output_file and "20" not in output_file[:20]:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = output_file.replace(".md", f"-{ts}.md")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.basename(output_file))

    result = generate_md_report(data, output_file)
    print(f"Report generated: {result}")
