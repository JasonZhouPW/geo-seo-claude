"""Centralized scoring logic for all GEO metrics.
All score calculations live here — SKILL.md references this module.
Weights and formulas are documented in docs/SCORING-STANDARDS.md.

Algorithm reference: docs/SCORING-STANDARDS.md v1.0.0 (2026-04-12)
"""

import re
from typing import List, Dict, Any, Optional, Tuple


# === WEIGHTS (source of truth) ===
WEIGHTS = {
    "ai_citability": 0.25,
    "brand_authority": 0.20,
    "content_quality": 0.20,
    "technical": 0.15,
    "structured_data": 0.10,
    "platform_optimization": 0.10,
}

# === Platform weights for brand authority ===
PLATFORM_WEIGHTS = {
    "youtube": 0.25,
    "reddit": 0.20,
    "wikipedia": 0.20,
    "linkedin": 0.15,
    "twitter": 0.10,
    "github": 0.10,
}

# === E-E-A-T dimension weights ===
EEAT_WEIGHTS = {
    "experience": 0.20,   # max 20 pts
    "expertise": 0.30,    # max 30 pts
    "authoritativeness": 0.25,  # max 25 pts
    "trustworthiness": 0.25,   # max 25 pts
}


# =============================================================================
# 1. AI CITABILITY SCORING (docs/SCORING-STANDARDS.md §2)
# =============================================================================

def score_passage(text: str, heading: str = "") -> Dict[str, Any]:
    """Score a passage for AI citability (0-100).

    Algorithm from SCORING-STANDARDS.md §2:
    - Answer Block Quality: 30 pts max
    - Self-Containment: 25 pts max
    - Structural Readability: 20 pts max
    - Statistical Density: 15 pts max
    - Uniqueness Signals: 10 pts max
    """
    text = text.strip()
    if not text:
        return {"score": 0, "grade": "F", "breakdown": {}}

    breakdown = {}

    # --- Answer Block Quality (30 pts max) ---
    aq_score = 0
    first_60_words = " ".join(text.split()[:60]).lower()

    # Definition pattern (15 pts)
    definition_patterns = [
        r"\b\w+\s+is\s+(?:a|an|the)\s",
        r"\b\w+\s+refers?\s+to\s",
        r"\b\w+\s+means?\s",
        r"\b\w+\s+defined\s+as\s",
    ]
    for pat in definition_patterns:
        if re.search(pat, text, re.IGNORECASE):
            aq_score += 15
            breakdown["definition"] = 15
            break

    # Answer in first 60 words (15 pts)
    answer_signals = [r"(?:is|are|was|were|means|refers)", r"\$", r"\d"]
    if any(re.search(s, first_60_words) for s in answer_signals):
        aq_score += 15
        breakdown["answer_in_first_60"] = 15

    # Question heading (10 pts)
    if heading.endswith("?"):
        aq_score += 10
        breakdown["question_heading"] = 10

    # Quotable claim (10 pts)
    quotable_patterns = [r"according to", r"research shows", r"studies show"]
    for pat in quotable_patterns:
        if re.search(pat, text, re.IGNORECASE):
            aq_score += 10
            breakdown["quotable_claim"] = 10
            break

    aq_score = min(30, aq_score)
    breakdown["answer_block_quality"] = aq_score

    # --- Self-Containment (25 pts max) ---
    sc_score = 0
    word_count = len(text.split())

    # Word count scoring
    if 134 <= word_count <= 167:
        sc_score += 10
        breakdown["word_count"] = "optimal"  # 10 pts
    elif 100 <= word_count <= 200:
        sc_score += 7
        breakdown["word_count"] = "good"  # 7 pts
    elif 80 <= word_count <= 250:
        sc_score += 4
        breakdown["word_count"] = "acceptable"  # 4 pts

    # Pronoun ratio (8 pts max)
    pronouns = re.findall(
        r"\b(?:it|they|them|their|this|that|these|those|he|she|his|her)\b",
        text.lower()
    )
    pronoun_ratio = len(pronouns) / word_count if word_count else 1
    if pronoun_ratio < 0.02:
        sc_score += 8
    elif pronoun_ratio < 0.04:
        sc_score += 5
    elif pronoun_ratio < 0.06:
        sc_score += 3
    breakdown["pronoun_ratio"] = round(pronoun_ratio, 4)

    # Named entities (7 pts max)
    proper_nouns = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    if len(proper_nouns) >= 3:
        sc_score += 7
    elif len(proper_nouns) >= 1:
        sc_score += 4
    breakdown["named_entities"] = len(proper_nouns)

    sc_score = min(25, sc_score)
    breakdown["self_containment"] = sc_score

    # --- Structural Readability (20 pts max) ---
    sr_score = 0
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    num_sentences = len(sentences)
    avg_sentence_len = word_count / num_sentences if num_sentences else 0

    if 10 <= avg_sentence_len <= 20:
        sr_score += 8
        breakdown["sentence_length"] = "optimal"  # 8 pts
    elif 8 <= avg_sentence_len <= 25:
        sr_score += 5
        breakdown["sentence_length"] = "good"  # 5 pts

    # List indicators (4 pts)
    list_patterns = [r"\bfirst\b", r"\bsecond\b", r"\bthird\b", r"\bfinally\b",
                     r"\badditionally\b", r"\blist\b"]
    if any(re.search(p, text, re.IGNORECASE) for p in list_patterns):
        sr_score += 4
        breakdown["list_indicators"] = 4

    # Numbered items (4 pts)
    numbered_patterns = [r"\d+\.", r"\d+\)", r"\bstep\s+\d+", r"\btip\s+\d+"]
    if any(re.search(p, text) for p in numbered_patterns):
        sr_score += 4
        breakdown["numbered_items"] = 4

    # Paragraph breaks (4 pts)
    if "\n" in text:
        sr_score += 4
        breakdown["paragraph_breaks"] = 4

    sr_score = min(20, sr_score)
    breakdown["structural_readability"] = sr_score

    # --- Statistical Density (15 pts max) ---
    stat_score = 0

    # Percentages (6 pts max)
    percentages = re.findall(r"\d+(?:\.\d+)?%", text)
    stat_score += min(6, len(percentages) * 3)
    breakdown["percentages"] = len(percentages)

    # Dollar amounts (5 pts max)
    dollars = re.findall(r"\$[\d,]+(?:\.\d{2})?", text)
    stat_score += min(5, len(dollars) * 3)
    breakdown["dollar_amounts"] = len(dollars)

    # Contextual numbers (4 pts max)
    context_patterns = [
        r"\d+\s+(?:users|customers|pages|sites|visitors|companies|items|products)"
    ]
    for pat in context_patterns:
        matches = re.findall(pat, text.lower())
        stat_score += min(4, len(matches) * 2)
        if matches:
            break
    breakdown["contextual_numbers"] = stat_score

    # Year references (2 pts)
    years = re.findall(r"\b20(?:2[3-9]|1\d)\b", text)
    if years:
        stat_score += 2
    breakdown["year_references"] = len(years)

    # Named sources (2 pts)
    named_sources = ["gartner", "forrester", "mckinsey", "google", "bloomberg",
                     "merrill", "deloitte", "pwc", "ey", "kPMG", "ibm", "microsoft"]
    if any(src in text.lower() for src in named_sources):
        stat_score += 2
        breakdown["named_sources"] = 2

    stat_score = min(15, stat_score)
    breakdown["statistical_density"] = stat_score

    # --- Uniqueness Signals (10 pts max) ---
    uniq_score = 0

    # Original research (5 pts)
    orig_patterns = [r"\bour research\b", r"\bour study\b", r"\bwe found\b",
                     r"\bwe analyzed\b", r"\bour data\b"]
    if any(re.search(p, text, re.IGNORECASE) for p in orig_patterns):
        uniq_score += 5
        breakdown["original_research"] = 5

    # Case study (3 pts)
    case_patterns = [r"\bcase study\b", r"\bfor example\b", r"\bfor instance\b",
                     r"\bin practice\b"]
    if any(re.search(p, text, re.IGNORECASE) for p in case_patterns):
        uniq_score += 3
        breakdown["case_study"] = 3

    # Tool mentions (2 pts)
    tool_patterns = [r"\busing\b", r"\bwith\b", r"\bvia\b", r"\bthrough\b"]
    if any(re.search(p + r"\s+[A-Z][a-z]+", text) for p in tool_patterns):
        uniq_score += 2
        breakdown["tool_mentions"] = 2

    uniq_score = min(10, uniq_score)
    breakdown["uniqueness"] = uniq_score

    # --- Total ---
    total = aq_score + sc_score + sr_score + stat_score + uniq_score

    # Grade
    if total >= 80:
        grade = "A"
    elif total >= 65:
        grade = "B"
    elif total >= 50:
        grade = "C"
    elif total >= 35:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": total,
        "grade": grade,
        "word_count": word_count,
        "breakdown": breakdown,
        "subscores": {
            "answer_block_quality": aq_score,
            "self_containment": sc_score,
            "structural_readability": sr_score,
            "statistical_density": stat_score,
            "uniqueness": uniq_score,
        }
    }


def compute_page_citability_score(pages: List[Dict]) -> Tuple[float, List[Dict]]:
    """Compute AI citability score for a page or pages.

    Algorithm from SCORING-STANDARDS.md §2.3:
    - Split page into blocks (paragraphs, >=50 words)
    - Score each block with score_passage()
    - Average across all blocks
    - Generate findings for D/F grade blocks

    Args:
        pages: List of page dicts with 'content' key (or 'text')

    Returns:
        Tuple of (score, findings)
    """
    if not pages:
        return 0.0, []

    all_scores = []
    findings = []

    for page in pages:
        content = page.get("content", page.get("text", ""))
        if not content:
            continue

        # Split into blocks (paragraphs >= 50 words)
        blocks = [b.strip() for b in content.split("\n\n") if len(b.split()) >= 50]

        if not blocks:
            # If no block meets threshold, use full content as single block
            if len(content.split()) >= 50:
                blocks = [content]

        for block in blocks:
            result = score_passage(block, heading=page.get("heading", ""))
            all_scores.append(result["score"])

            # Generate findings for D/F grades
            if result["grade"] in ("D", "F"):
                word_count = result.get("word_count", 0)
                findings.append({
                    "type": "citability",
                    "severity": "high" if result["grade"] == "F" else "medium",
                    "message": f"Low citability block ({result['grade']}, {word_count} words)",
                    "suggestion": "Add definitions, statistics, or structured content to improve AI citability",
                })

    if not all_scores:
        return 0.0, [{"type": "citability", "severity": "high",
                      "message": "No content blocks found", "suggestion": ""}]

    avg_score = sum(all_scores) / len(all_scores)
    return round(avg_score, 1), findings


# =============================================================================
# 2. BRAND AUTHORITY SCORING (docs/SCORING-STANDARDS.md §3)
# =============================================================================

def compute_brand_authority_score(
    platforms_data: Dict[str, bool],
    pages_data: List[Dict]
) -> Tuple[float, List[Dict]]:
    """Compute brand authority score (0-100).

    Algorithm from SCORING-STANDARDS.md §3:
    - Platform presence: Σ(platform_found × platform_weight × 100)
    - Brand signals: +30 max (contact info, about page, team, social links)
    - Brand signals averaged across all pages, capped at 30
    """
    # Platform presence score
    platform_score = 0.0
    for platform, found in platforms_data.items():
        weight = PLATFORM_WEIGHTS.get(platform.lower(), 0)
        if found:
            platform_score += weight * 100

    # Brand signals from content
    brand_signals_score = _compute_brand_signals(pages_data)

    total = platform_score + brand_signals_score
    total = min(100, max(0, total))

    # Generate findings for missing platforms
    findings = []
    missing = [p for p, found in platforms_data.items() if not found]
    if missing:
        findings.append({
            "type": "brand_authority",
            "severity": "medium",
            "message": f"Missing platform presence: {', '.join(missing)}",
            "suggestion": "Establish presence on key platforms to improve brand authority",
        })

    return round(total, 1), findings


def _compute_brand_signals(pages_data: List[Dict]) -> float:
    """Compute brand signals score from page content (+30 max)."""
    if not pages_data:
        return 0.0

    signal_keywords = {
        "contact": [r"\baddress\b", r"\bphone\b", r"\bemail\b", r"\bcontact\b"],
        "about": [r"\babout\b"],
        "team": [r"\bteam\b", r"\bfounder\b", r"\bceo\b", r"\bemployees\b", r"\bstaff\b"],
        "social": [r"twitter\.com", r"linkedin\.com", r"facebook\.com", r"github\.com"],
    }

    page_scores = []
    for page in pages_data:
        content = page.get("content", page.get("text", ""))
        if not content:
            continue

        score = 0
        content_lower = content.lower()
        first_500 = content[:500].lower()

        # Contact info (10 pts)
        if any(re.search(p, content_lower) for p in signal_keywords["contact"]):
            score += 10

        # About page (10 pts)
        title = page.get("title", "").lower()
        if "about" in title or "about" in first_500:
            score += 10

        # Team mentions (10 pts)
        if any(re.search(p, content_lower) for p in signal_keywords["team"]):
            score += 10

        # Social links (10 pts)
        if any(re.search(p, content_lower) for p in signal_keywords["social"]):
            score += 10

        page_scores.append(min(10 + 10 + 10 + 10, score))

    if not page_scores:
        return 0.0

    # Average across pages, capped at 30
    avg = sum(page_scores) / len(page_scores)
    return min(30, avg)


# =============================================================================
# 3. CONTENT QUALITY E-E-A-T SCORING (docs/SCORING-STANDARDS.md §4)
# =============================================================================

def compute_content_quality_score(
    pages_data: List[Dict],
    business_type: Optional[str] = None
) -> Tuple[float, List[Dict]]:
    """Compute E-E-A-T content quality score (0-100).

    Algorithm from SCORING-STANDARDS.md §4:
    - Experience: 20 pts max (stop after 4 signals)
    - Expertise: 30 pts max (stop after 8 signals)
    - Authoritativeness: 25 pts max (stop after 5 signals)
    - Trustworthiness: 25 pts max (stop after 7 signals)
    - Depth bonus: +10/>1000 words, +5/>500 words, -10/<100 words
    - Final: (E-E-A-T × 0.8) + (base × 0.2) + depth_bonus
    """
    if not pages_data:
        return 0.0, [{"type": "content_quality", "severity": "high",
                      "message": "No pages to evaluate", "suggestion": ""}]

    experience_keywords = [
        r"\bwe have\b", r"\bour team\b", r"\bour product\b",
        r"\byears of experience\b", r"\bsince 20\d{2}\b",
        r"\bfounded\b", r"\bpractical\b", r"\bhands-on\b", r"\bcase study\b"
    ]
    expertise_keywords = [
        r"\bspecialized\b", r"\bcertified\b", r"\bprofessional\b",
        r"\bexpert\b", r"\badvanced\b", r"\bcomprehensive\b",
        r"\bbest practices\b", r"\bmethodology\b", r"\bframework\b"
    ]
    authority_keywords = [
        r"\baccording to\b", r"\bresearch shows\b", r"\bstudies indicate\b",
        r"\bdata shows\b", r"\bindustry report\b", r"\bwhitepaper\b",
        r"\bcase study\b", r"\btestimonial\b"
    ]
    trustworthiness_keywords = [
        r"\bguarantee\b", r"\bwarranty\b", r"\bsecure\b", r"\bprivacy policy\b",
        r"\bterms of service\b", r"\bcontact us\b", r"\babout us\b",
        r"\bmission\b", r"\bno spam\b", r"\bunsubscribe\b"
    ]

    total_experience = 0
    total_expertise = 0
    total_authority = 0
    total_trust = 0
    depth_bonus = 0
    total_words = 0

    for page in pages_data:
        content = page.get("content", page.get("text", ""))
        if not content:
            continue

        content_lower = content.lower()
        word_count = len(content.split())
        total_words += word_count

        # Experience (5 pts each, max 20, stop after 4)
        exp_count = 0
        for kw in experience_keywords:
            if re.search(kw, content_lower):
                exp_count += 1
                if exp_count >= 4:
                    break
        total_experience += min(20, exp_count * 5)

        # Expertise (4 pts each, max 30, stop after 8)
        exp_skill_count = 0
        for kw in expertise_keywords:
            if re.search(kw, content_lower):
                exp_skill_count += 1
                if exp_skill_count >= 8:
                    break
        total_expertise += min(30, exp_skill_count * 4)

        # Authoritativeness (5 pts each, max 25, stop after 5)
        auth_count = 0
        for kw in authority_keywords:
            if re.search(kw, content_lower):
                auth_count += 1
                if auth_count >= 5:
                    break
        total_authority += min(25, auth_count * 5)

        # Trustworthiness (4 pts each, max 25, stop after 7)
        trust_count = 0
        for kw in trustworthiness_keywords:
            if re.search(kw, content_lower):
                trust_count += 1
                if trust_count >= 7:
                    break
        total_trust += min(25, trust_count * 4)

    # Depth bonus
    avg_words = total_words / len(pages_data) if pages_data else 0
    if avg_words > 1000:
        depth_bonus = 10
    elif avg_words > 500:
        depth_bonus = 5
    elif avg_words < 100:
        depth_bonus = -10

    # E-E-A-T total (capped at 100)
    eeat_total = min(100, total_experience + total_expertise +
                     total_authority + total_trust)

    # Final formula from spec: (E-E-A-T × 0.8) + (base × 0.2) + depth_bonus
    # base_score = 50 (midpoint)
    final_score = (eeat_total * 0.8) + (50 * 0.2) + depth_bonus
    final_score = min(100, max(0, final_score))

    findings = []
    if avg_words < 100:
        findings.append({
            "type": "content_quality",
            "severity": "high",
            "message": f"Thin content: {avg_words:.0f} avg words per page",
            "suggestion": "Expand content to >500 words for better E-E-A-T signals",
        })
    elif avg_words < 500:
        findings.append({
            "type": "content_quality",
            "severity": "medium",
            "message": f"Content could be deeper: {avg_words:.0f} avg words per page",
            "suggestion": "Consider expanding key pages to >1000 words",
        })

    return round(final_score, 1), findings


# =============================================================================
# 4. TECHNICAL SEO SCORING (docs/SCORING-STANDARDS.md §5)
# =============================================================================

def compute_technical_seo_score(pages_data: List[Dict]) -> Tuple[float, List[Dict]]:
    """Compute technical SEO score (0-100).

    Algorithm from SCORING-STANDARDS.md §5:
    - Base: 50 pts
    - Title tag: missing=-15, <30chars=-5, >60chars=-5
    - Meta description: missing=-10, <120chars=-5
    - H1: missing=-15
    - Word count: <100=-10, >1000=+10
    - Schema markup: has=+10, missing=-5
    """
    if not pages_data:
        return 0.0, [{"type": "technical_seo", "severity": "high",
                      "message": "No pages to evaluate", "suggestion": ""}]

    page_scores = []
    all_findings = []

    for page in pages_data:
        score = 50
        findings = []

        title = page.get("title", "")
        meta_desc = page.get("meta_description", page.get("description", ""))
        h1 = page.get("h1", page.get("heading", ""))
        content = page.get("content", page.get("text", ""))
        has_schema = page.get("has_schema", False)
        word_count = len(content.split()) if content else 0

        # Title tag
        if not title:
            score -= 15
            findings.append({"element": "title", "severity": "high",
                             "issue": "missing", "deduction": -15})
        elif len(title) < 30:
            score -= 5
            findings.append({"element": "title", "severity": "medium",
                             "issue": "too_short", "deduction": -5})
        elif len(title) > 60:
            score -= 5
            findings.append({"element": "title", "severity": "low",
                             "issue": "too_long", "deduction": -5})

        # Meta description
        if not meta_desc:
            score -= 10
            findings.append({"element": "meta_description", "severity": "medium",
                             "issue": "missing", "deduction": -10})
        elif len(meta_desc) < 120:
            score -= 5
            findings.append({"element": "meta_description", "severity": "low",
                             "issue": "too_short", "deduction": -5})

        # H1
        if not h1:
            score -= 15
            findings.append({"element": "h1", "severity": "high",
                             "issue": "missing", "deduction": -15})

        # Word count
        if word_count < 100:
            score -= 10
            findings.append({"element": "word_count", "severity": "medium",
                             "issue": "too_thin", "deduction": -10})
        elif word_count > 1000:
            score += 10

        # Schema
        if has_schema:
            score += 10
        else:
            score -= 5

        score = min(100, max(0, score))
        page_scores.append(score)

        for f in findings:
            all_findings.append({
                "type": "technical_seo",
                "severity": f["severity"],
                "message": f"Page '{title[:30]}...': {f['element']} {f['issue']}",
                "suggestion": f"Deduction: {f['deduction']} pts",
            })

    avg_score = sum(page_scores) / len(page_scores) if page_scores else 0
    return round(avg_score, 1), all_findings


# =============================================================================
# 5. SCHEMA.ORG STRUCTURED DATA SCORING (docs/SCORING-STANDARDS.md §6)
# =============================================================================

IMPORTANT_SCHEMA_TYPES = [
    "Organization", "WebSite", "Article", "FAQPage",
    "HowTo", "Product", "LocalBusiness",
]

def compute_schema_score(pages_data: List[Dict]) -> Tuple[float, List[Dict]]:
    """Compute schema.org structured data score (0-100).

    Algorithm from SCORING-STANDARDS.md §6:
    - Base: 50 pts
    - Each important schema type present: +10 pts
    - Penalties: total < 3 = -20, total < 5 = -10
    """
    if not pages_data:
        return 0.0, [{"type": "structured_data", "severity": "high",
                      "message": "No pages to evaluate", "suggestion": ""}]

    found_types = set()
    total_schema_count = 0

    for page in pages_data:
        schemas = page.get("schemas", page.get("schema_types", []))
        if isinstance(schemas, str):
            schemas = [schemas]
        for s in schemas:
            s_type = s if isinstance(s, str) else s.get("@type", "")
            if s_type:
                found_types.add(s_type)
                total_schema_count += 1

    # Score calculation
    score = 50
    for schema_type in IMPORTANT_SCHEMA_TYPES:
        if schema_type in found_types:
            score += 10

    # Penalties
    if total_schema_count < 3:
        score -= 20
    elif total_schema_count < 5:
        score -= 10

    score = min(100, max(0, score))

    findings = []
    if total_schema_count < 3:
        findings.append({
            "type": "structured_data",
            "severity": "high",
            "message": f"Very few schemas detected ({total_schema_count})",
            "suggestion": "Add Organization, WebSite, and Article schema types",
        })
    elif total_schema_count < 5:
        findings.append({
            "type": "structured_data",
            "severity": "medium",
            "message": f"Limited schema diversity ({total_schema_count} types)",
            "suggestion": "Consider adding FAQPage or HowTo schema",
        })

    missing = [t for t in IMPORTANT_SCHEMA_TYPES if t not in found_types]
    if missing:
        findings.append({
            "type": "structured_data",
            "severity": "low",
            "message": f"Missing recommended schemas: {', '.join(missing)}",
            "suggestion": "These schemas can improve AI crawler understanding",
        })

    return round(score, 1), findings


# =============================================================================
# 6. PLATFORM OPTIMIZATION SCORING (docs/SCORING-STANDARDS.md §7)
# =============================================================================

def compute_platform_optimization_score(pages_data: List[Dict]) -> Tuple[float, List[Dict]]:
    """Compute platform optimization score (0-100).

    Algorithm from SCORING-STANDARDS.md §7:
    - Social sharing indicators: +5
    - Internal links >5: +5
    - Internal links <2: finding
    """
    if not pages_data:
        return 0.0, []

    total_score = 0
    all_findings = []

    for page in pages_data:
        content = page.get("content", page.get("text", ""))
        if not content:
            continue

        score = 0

        # Social sharing indicators (+5)
        social_patterns = [
            r"share on twitter", r"share on facebook", r"facebook\.com/sharer",
            r"twitter\.com/intent", r"\blinkedin\.com/share\b"
        ]
        if any(re.search(p, content, re.IGNORECASE) for p in social_patterns):
            score += 5

        # Internal links
        internal_link_pattern = r'<a\s+href="/[^"]*"'
        internal_links = re.findall(internal_link_pattern, content)
        # Also try plain text URL detection
        if not internal_links:
            internal_links = re.findall(r'href="/[^"]+"', content)

        if len(internal_links) > 5:
            score += 5
        elif len(internal_links) < 2:
            all_findings.append({
                "type": "platform_optimization",
                "severity": "low",
                "message": f"Few internal links ({len(internal_links)}) on page",
                "suggestion": "Add more internal links to improve site structure",
            })

        total_score += score

    avg_score = total_score / len(pages_data) if pages_data else 0
    return round(avg_score, 1), all_findings


# =============================================================================
# LEGACY / COMPATIBILITY FUNCTIONS
# =============================================================================

def compute_citability_score(passage_score: float, word_count: int,
                              has_statistics: bool, has_definitions: bool) -> float:
    """Legacy compatibility function.

    New code should use score_passage() and compute_page_citability_score().
    This function is kept for backward compatibility with existing tests.
    """
    base = passage_score * 0.4
    word_bonus = 20 if 134 <= word_count <= 167 else (10 if word_count > 100 else 0)
    stat_bonus = 15 if has_statistics else 0
    def_bonus = 10 if has_definitions else 0
    return min(100, base + word_bonus + stat_bonus + def_bonus)


def compute_eeat_score(experience: float, expertise: float,
                       authority: float, trustworthiness: float) -> float:
    """Compute E-E-A-T composite score 0-100.

    Legacy compatibility - for full E-E-A-T scoring use compute_content_quality_score().
    """
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
        platform: Dict of platform-specific scores (averaged for platform_optimization)
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
