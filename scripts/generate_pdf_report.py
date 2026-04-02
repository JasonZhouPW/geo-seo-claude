#!/usr/bin/env python3
"""
GEO-SEO PDF Report Generator
Generates professional PDF reports following the geo_report_template design.
Uses ReportLab canvas API with the brand color palette.

Usage:
    python generate_pdf_report.py <json_data_file> [output_file.pdf]
"""

import sys
import json
import os
import math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line, Wedge
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# AutoGEO rules integration - add script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from autogeo_rules import get_rules_for_audit, rules_to_action_plan
    HAS_AUTOGEO_RULES = True
except ImportError:
    HAS_AUTOGEO_RULES = False

# Register Chinese font (use system font on macOS)
try:
    pdfmetrics.registerFont(TTFont("Chinese", "/System/Library/Fonts/STHeiti Light.ttc"))
    pdfmetrics.registerFont(TTFont("ChineseBold", "/System/Library/Fonts/STHeiti Medium.ttc"))
    HAS_CJK_FONT = True
except:
    HAS_CJK_FONT = False

def has_cjk(text):
    """Check if text contains CJK characters"""
    return any(ord(c) > 0x4E00 for c in text)

def get_font_for_text(font_regular="Helvetica", font_bold="Helvetica-Bold"):
    """Return appropriate font for CJK text"""
    if HAS_CJK_FONT:
        return ("Chinese", "ChineseBold")
    return (font_regular, font_bold)

def get_action_text(item):
    """Extract display text from an action item (handles dict with 'action' or 'rule' key, or plain string)."""
    if isinstance(item, dict):
        # Try 'action' key first (original format), then 'rule' (AutoGEO format)
        if "action" in item:
            return item["action"]
        elif "rule" in item:
            return item["rule"]
        else:
            # Fallback: return a readable summary
            return str(item)
    return str(item)

# ── Brand Palette (from geo_report_template) ──────────────────────────────────
NAVY       = colors.HexColor("#0D1B2A")
DARK_BLUE  = colors.HexColor("#1A2E44")
ACCENT     = colors.HexColor("#0066CC")
ACCENT2    = colors.HexColor("#00A3E0")
GOLD       = colors.HexColor("#F0A500")
LIGHT_BG   = colors.HexColor("#F4F7FB")
BORDER     = colors.HexColor("#D0DCE8")
TEXT_DARK  = colors.HexColor("#1A1A2E")
TEXT_MID   = colors.HexColor("#4A5568")
TEXT_LIGHT = colors.HexColor("#718096")
WHITE      = colors.white
GREEN      = colors.HexColor("#00875A")
ORANGE     = colors.HexColor("#E86020")
RED_SOFT   = colors.HexColor("#CC2936")
SCORE_BG   = colors.HexColor("#EBF4FF")

W, H = A4

# ── Helpers (from geo_report_template) ────────────────────────────────────────

def draw_rect(c, x, y, w, h, fill=None, stroke=None, radius=0, lw=0.5):
    c.saveState()
    if fill:   c.setFillColor(fill)
    if stroke: c.setStrokeColor(stroke); c.setLineWidth(lw)
    else:      c.setStrokeColor(colors.transparent)
    c.roundRect(x, y, w, h, radius, fill=bool(fill), stroke=bool(stroke))
    c.restoreState()

def label(c, text, x, y, size=8, color=TEXT_LIGHT, font="Helvetica", align="left"):
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "center": c.drawCentredString(x, y, text)
    elif align == "right": c.drawRightString(x, y, text)
    else: c.drawString(x, y, text)
    c.restoreState()

def score_ring(c, cx, cy, score, size=60, label_text=""):
    """Draw a circular score gauge."""
    r_outer = size / 2
    r_inner = r_outer * 0.68
    angle = 360 * score / 100

    # Background ring
    c.saveState()
    c.setStrokeColor(BORDER)
    c.setLineWidth(r_outer - r_inner)
    c.circle(cx, cy, (r_outer + r_inner) / 2, stroke=1, fill=0)
    c.restoreState()

    # Score arc
    if score > 0:
        c.saveState()
        steps = max(int(angle), 1)
        for i in range(steps):
            a1 = 90 - i
            a2 = 90 - i - 1
            d = Drawing(0, 0)
            w = Wedge(cx, cy, r_outer, a1, a2, radius1=r_inner)
            if score >= 70:
                w.fillColor = ACCENT
            elif score >= 50:
                w.fillColor = GOLD
            else:
                w.fillColor = ORANGE
            w.strokeColor = None
            d.add(w)
            renderPDF.draw(d, c, 0, 0)
        c.restoreState()

    # Center text
    c.saveState()
    c.setFont("Helvetica-Bold", size * 0.28)
    c.setFillColor(TEXT_DARK)
    c.drawCentredString(cx, cy + size * 0.04, str(score))
    c.setFont("Helvetica", size * 0.14)
    c.setFillColor(TEXT_LIGHT)
    c.drawCentredString(cx, cy - size * 0.14, "/100")
    c.restoreState()

    if label_text:
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(TEXT_MID)
        c.drawCentredString(cx, cy - size / 2 - 10, label_text)
        c.restoreState()

def status_pill(c, x, y, status, w=52, h=13):
    if status == "Good":
        bg, fg = colors.HexColor("#E3F9E5"), GREEN
    elif status == "Excellent":
        bg, fg = colors.HexColor("#E3F9E5"), GREEN
    elif status == "Moderate":
        bg, fg = colors.HexColor("#FFF3E0"), GOLD
    elif status == "Fair":
        bg, fg = colors.HexColor("#FFF3E0"), ORANGE
    else:
        bg, fg = colors.HexColor("#FFEBEE"), RED_SOFT
    draw_rect(c, x, y, w, h, fill=bg, radius=6)
    c.saveState()
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(fg)
    c.drawCentredString(x + w/2, y + 4, status)
    c.restoreState()

def bar_mini(c, x, y, score, bar_w=80, bar_h=5):
    draw_rect(c, x, y, bar_w, bar_h, fill=BORDER, radius=2)
    filled = bar_w * score / 100
    col = ACCENT if score >= 70 else GOLD if score >= 50 else ORANGE
    draw_rect(c, x, y, filled, bar_h, fill=col, radius=2)

def section_header(c, y, title, subtitle=""):
    draw_rect(c, 18*mm, y, W - 36*mm, 20, fill=LIGHT_BG, radius=3)
    c.saveState()
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(NAVY)
    c.drawString(22*mm, y + 6, title)
    if subtitle:
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_LIGHT)
        c.drawRightString(W - 20*mm, y + 6, subtitle)
    c.restoreState()
    return y - 10

def page_footer(c, page_num, total, url="", brand=""):
    c.saveState()
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(18*mm, 14*mm, W - 18*mm, 14*mm)
    c.setFillColor(TEXT_LIGHT)
    # Use CJK font for brand names with Chinese characters
    font_reg, font_bold = get_font_for_text()
    c.setFont(font_reg, 7)
    footer_text = f"GEO Analysis Report  ·  {brand} ({url})  ·  Confidential"
    c.drawString(18*mm, 10*mm, footer_text)
    c.drawRightString(W - 18*mm, 10*mm, f"Page {page_num} of {total}")
    c.restoreState()

def word_wrap_text(c, text, max_w, font="Helvetica", size=8.5):
    """Word wrap text and return list of lines."""
    words = text.split()
    line, lines = [], []
    c.setFont(font, size)
    for w in words:
        test = " ".join(line + [w])
        if c.stringWidth(test, font, size) < max_w:
            line.append(w)
        else:
            lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))
    return lines

def get_score_label(score):
    """Return label based on score value."""
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 55:
        return "Moderate"
    elif score >= 40:
        return "Below Average"
    else:
        return "Needs Work"

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — COVER
# ══════════════════════════════════════════════════════════════════════════════

def draw_cover(c, data):
    url = data.get("url", "https://example.com")
    brand_name = data.get("brand_name", url.replace("https://", "").replace("http://", "").split("/")[0])
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    geo_score = data.get("geo_score", 0)
    scores = data.get("scores", {})
    executive_summary = data.get("executive_summary", "")

    # Format date
    if "-" in date:
        try:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y")
        except:
            formatted_date = date
    else:
        formatted_date = date

    tier_label = get_score_label(geo_score)

    # Full dark header band
    draw_rect(c, 0, H - 120*mm, W, 120*mm, fill=NAVY)

    # Decorative accent bars
    draw_rect(c, 0, H - 120*mm, W, 3, fill=ACCENT2)
    draw_rect(c, 0, H - 2, W, 2, fill=ACCENT)

    # Dot grid decoration
    c.saveState()
    c.setFillColor(colors.HexColor("#1E2D3D"))
    for row in range(12):
        for col in range(20):
            c.circle(col * 14 * mm + 7*mm, H - 5*mm - row * 10*mm, 1.5, fill=1, stroke=0)
    c.restoreState()

    # REPORT TYPE tag
    draw_rect(c, 18*mm, H - 28*mm, 55, 16, fill=ACCENT, radius=8)
    c.saveState()
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(WHITE)
    c.drawString(22*mm, H - 23.5*mm, "GEO AUDIT REPORT")
    c.restoreState()

    # Main title
    c.saveState()
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(WHITE)
    c.drawString(18*mm, H - 52*mm, "Generative Engine")
    c.drawString(18*mm, H - 64*mm, "Optimization Audit")
    c.restoreState()

    # Divider line
    c.saveState()
    c.setStrokeColor(ACCENT2)
    c.setLineWidth(1.5)
    c.line(18*mm, H - 70*mm, 80*mm, H - 70*mm)
    c.restoreState()

    # Subtitle
    c.saveState()
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#A0B4C8"))
    c.drawString(18*mm, H - 78*mm, f"for {brand_name}")
    c.restoreState()

    # Meta info block (right side of header)
    meta = [
        ("Website", url),
        ("Analysis Date", formatted_date),
        ("Classification", "Confidential"),
    ]
    mx = W - 70*mm
    my = H - 38*mm
    for k, v in meta:
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#7A9AB5"))
        c.drawString(mx, my, k.upper())
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(WHITE)
        # Truncate long URLs
        display_v = v if len(v) <= 30 else v[:27] + "..."
        c.drawString(mx, my - 10, display_v)
        c.restoreState()
        my -= 26

    # ── SCORE HERO ────────────────────────────────────────────────────────────
    sy = H - 175*mm
    draw_rect(c, 18*mm, sy, W - 36*mm, 62*mm, fill=WHITE, radius=8, stroke=BORDER, lw=0.5)

    # Large score ring
    score_ring(c, 55*mm, sy + 31*mm, geo_score, size=80)

    # Score label
    c.saveState()
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(NAVY)
    c.drawString(95*mm, sy + 44*mm, "Overall GEO Score")
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_MID)
    c.drawString(95*mm, sy + 36*mm, "Placing in the ")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GREEN)
    tier_w = c.stringWidth(tier_label, "Helvetica-Bold", 9)
    c.drawString(95*mm + c.stringWidth("Placing in the ", "Helvetica", 9), sy + 36*mm, tier_label)
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_MID)
    c.drawString(95*mm + c.stringWidth("Placing in the ", "Helvetica", 9) + tier_w, sy + 36*mm, " tier")
    c.restoreState()

    # Tier bar
    tiers = [("Needs Work", "0–49", RED_SOFT), ("Fair", "50–59", ORANGE), ("Good", "60–79", ACCENT), ("Excellent", "80–100", GREEN)]
    tx = 95*mm
    ty = sy + 26*mm
    for name, rng, col in tiers:
        draw_rect(c, tx, ty, 30, 15, fill=col if name == tier_label else LIGHT_BG, radius=4)
        c.saveState()
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(WHITE if name == tier_label else TEXT_MID)
        c.drawCentredString(tx + 15, ty + 8, name)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(tx + 15, ty + 2, rng)
        c.restoreState()
        tx += 35

    # Mini component scores
    ai_citability = scores.get("ai_citability", 0)
    brand_authority = scores.get("brand_authority", 0)
    content_eeat = scores.get("content_eeat", 0)
    technical = scores.get("technical", 0)
    schema_score = scores.get("schema", 0)
    platform_optimization = scores.get("platform_optimization", 0)

    comps = [
        ("AI Citability", ai_citability),
        ("Brand Authority", brand_authority),
        ("Content & E-E-A-T", content_eeat),
        ("Technical", technical),
        ("Structured Data", schema_score),
        ("Platform Opt.", platform_optimization),
    ]
    cx_start = 18*mm + 6
    cy2 = sy + 10*mm
    cw = (W - 36*mm - 12) / 6
    for i, (name, sc) in enumerate(comps):
        bx = cx_start + i * cw
        # mini gauge
        draw_rect(c, bx + 2, cy2, cw - 10, 8, fill=BORDER, radius=2)
        fill_w = (cw - 10) * sc / 100
        col = ACCENT if sc >= 70 else GOLD if sc >= 50 else ORANGE
        draw_rect(c, bx + 2, cy2, fill_w, 8, fill=col, radius=2)
        c.saveState()
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(NAVY)
        c.drawCentredString(bx + cw/2 - 2, cy2 + 11, f"{sc}")
        c.setFont("Helvetica", 6)
        c.setFillColor(TEXT_LIGHT)
        c.drawCentredString(bx + cw/2 - 2, cy2 - 8, name)
        c.restoreState()

    # ── EXECUTIVE SUMMARY ─────────────────────────────────────────────────────
    ey = sy - 15
    c.saveState()
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(NAVY)
    c.drawString(18*mm, ey, "Executive Summary")
    c.setStrokeColor(ACCENT)
    c.setLineWidth(2)
    c.line(18*mm, ey - 3, 60*mm, ey - 3)
    c.restoreState()

    # Build summary text from data or use provided
    if executive_summary:
        summary = executive_summary
    else:
        summary = (
            f"This report presents the findings of a comprehensive Generative Engine Optimization (GEO) audit "
            f"conducted on {brand_name} ({url}). The analysis evaluated the website's readiness for "
            f"AI-powered search engines including Google AI Overviews, ChatGPT, Perplexity, Gemini, and Bing Copilot. "
            f"The overall GEO Readiness Score is {geo_score}/100, placing the site in the {tier_label} tier."
        )

    text_y = ey - 16
    max_w = W - 36*mm
    lines = word_wrap_text(c, summary, max_w, "Helvetica", 8.5)

    c.saveState()
    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_MID)
    for ln in lines:
        c.drawString(18*mm, text_y, ln)
        text_y -= 13
    c.restoreState()

    page_footer(c, 1, 5, url, brand_name)
    c.showPage()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — SCORE BREAKDOWN & AI PLATFORM READINESS
# ══════════════════════════════════════════════════════════════════════════════

def draw_page2(c, data):
    url = data.get("url", "")
    brand_name = data.get("brand_name", "")
    scores = data.get("scores", {})
    platforms = data.get("platforms", {})
    geo_score = data.get("geo_score", 0)
    tier_label = get_score_label(geo_score)

    ai_citability = scores.get("ai_citability", 0)
    brand_authority = scores.get("brand_authority", 0)
    content_eeat = scores.get("content_eeat", 0)
    technical = scores.get("technical", 0)
    schema_score = scores.get("schema", 0)
    platform_opt = scores.get("platform_optimization", 0)

    # GEO Impression Score
    geo_impression = data.get("geo_impression_score", {})
    impression_score = int(geo_impression.get("combined_score", 0) * 100) if geo_impression else 0
    impression_position = geo_impression.get("position_score", 0)
    impression_word_count = geo_impression.get("word_count_score", 0)
    citation_count = geo_impression.get("citation_count", 0)
    impression_recommendations = geo_impression.get("recommendations", [])

    y = H - 20*mm

    # Page header strip
    draw_rect(c, 0, H - 14*mm, W, 14*mm, fill=NAVY)
    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(18*mm, H - 9*mm, "GEO Score Breakdown")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#A0B4C8"))
    c.drawRightString(W - 18*mm, H - 9*mm, f"{brand_name} · {url}")
    c.restoreState()

    y = H - 26*mm

    # ── COMPONENT SCORE TABLE ─────────────────────────────────────────────────
    y = section_header(c, y, "GEO Score Breakdown", "Weighted component analysis")
    y -= 14

    # Calculate weighted points
    score_breakdown = data.get("score_breakdown", {})

    if impression_score > 0:
        # Updated weights with GEO Impression Score (14%)
        if score_breakdown:
            comps_data = [
                ("AI Citability & Visibility",  ai_citability, 22, score_breakdown.get("ai_citability", {}).get("points", ai_citability * 0.22)),
                ("Brand Authority Signals",     brand_authority, 18, score_breakdown.get("brand_authority", {}).get("points", brand_authority * 0.18)),
                ("Content Quality & E-E-A-T",   content_eeat, 18, score_breakdown.get("content_quality", {}).get("points", content_eeat * 0.18)),
                ("Technical Foundations",       technical, 12, score_breakdown.get("technical", {}).get("points", technical * 0.12)),
                ("Structured Data",             schema_score, 8, score_breakdown.get("structured_data", {}).get("points", schema_score * 0.08)),
                ("Platform Optimization",       platform_opt, 8, score_breakdown.get("platform_optimization", {}).get("points", platform_opt * 0.08)),
                ("GEO Impression Score",        impression_score, 14, impression_score * 0.14),
            ]
        else:
            comps_data = [
                ("AI Citability & Visibility",  ai_citability, 22, ai_citability * 0.22),
                ("Brand Authority Signals",     brand_authority, 18, brand_authority * 0.18),
                ("Content Quality & E-E-A-T",   content_eeat, 18, content_eeat * 0.18),
                ("Technical Foundations",       technical, 12, technical * 0.12),
                ("Structured Data",             schema_score, 8, schema_score * 0.08),
                ("Platform Optimization",       platform_opt, 8, platform_opt * 0.08),
                ("GEO Impression Score",        impression_score, 14, impression_score * 0.14),
            ]
    else:
        if score_breakdown:
            comps_data = [
                ("AI Citability & Visibility",  ai_citability, 25, score_breakdown.get("ai_citability", {}).get("points", ai_citability * 0.25)),
                ("Brand Authority Signals",     brand_authority, 20, score_breakdown.get("brand_authority", {}).get("points", brand_authority * 0.20)),
                ("Content Quality & E-E-A-T",   content_eeat, 20, score_breakdown.get("content_quality", {}).get("points", content_eeat * 0.20)),
                ("Technical Foundations",       technical, 15, score_breakdown.get("technical", {}).get("points", technical * 0.15)),
                ("Structured Data",             schema_score, 10, score_breakdown.get("structured_data", {}).get("points", schema_score * 0.10)),
                ("Platform Optimization",       platform_opt, 10, score_breakdown.get("platform_optimization", {}).get("points", platform_opt * 0.10)),
            ]
        else:
            comps_data = [
                ("AI Citability & Visibility",  ai_citability, 25, ai_citability * 0.25),
                ("Brand Authority Signals",     brand_authority, 20, brand_authority * 0.20),
                ("Content Quality & E-E-A-T",   content_eeat, 20, content_eeat * 0.20),
                ("Technical Foundations",       technical, 15, technical * 0.15),
                ("Structured Data",             schema_score, 10, schema_score * 0.10),
                ("Platform Optimization",       platform_opt, 10, platform_opt * 0.10),
            ]

    comps = []
    for name, score, wt, weighted in comps_data:
        status = get_score_label(score)
        comps.append((name, score, wt, weighted, status))

    # Header row
    cols = [18*mm, 82*mm, 116*mm, 137*mm, 155*mm, 175*mm]
    headers = ["Component", "Score", "Weight", "Weighted", "Status"]
    c.saveState()
    draw_rect(c, 18*mm, y - 2, W - 36*mm, 16, fill=DARK_BLUE, radius=3)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(WHITE)
    for i, h in enumerate(headers):
        c.drawString(cols[i] + 4, y + 4, h)
    c.restoreState()
    y -= 18

    for idx, (name, score, wt, weighted, status) in enumerate(comps):
        row_bg = LIGHT_BG if idx % 2 == 0 else WHITE
        draw_rect(c, 18*mm, y - 2, W - 36*mm, 22, fill=row_bg)

        # Component name
        c.saveState()
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(TEXT_DARK)
        c.drawString(cols[0] + 4, y + 8, name)
        c.restoreState()

        # Score with bar
        bar_mini(c, cols[1] + 4, y + 8, score, bar_w=28, bar_h=4)
        c.saveState()
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(NAVY)
        c.drawString(cols[1] + 36, y + 6, f"{score}/100")
        c.restoreState()

        # Weight
        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MID)
        c.drawString(cols[2] + 4, y + 6, f"{wt}%")

        # Weighted
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(NAVY)
        c.drawString(cols[3] + 4, y + 6, f"{weighted:.1f}")
        c.restoreState()

        # Status pill
        status_pill(c, cols[4] + 4, y + 3, status, w=50, h=14)

        y -= 24

    # Total row
    draw_rect(c, 18*mm, y - 2, W - 36*mm, 20, fill=NAVY, radius=3)
    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(cols[0] + 4, y + 6, "OVERALL GEO SCORE")
    c.drawString(cols[3] + 4, y + 6, f"{geo_score}")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT2)
    c.drawString(cols[4] + 4, y + 6, f"{tier_label}  ✓")
    c.restoreState()
    y -= 30

    # ── AI PLATFORM READINESS ─────────────────────────────────────────────────
    y = section_header(c, y, "AI Platform Readiness", "Likelihood of citation per platform")
    y -= 14

    platforms_list = [
        ("Google AI Overviews", platforms.get("Google AI Overviews", 0)),
        ("ChatGPT",             platforms.get("ChatGPT", 0)),
        ("Perplexity",          platforms.get("Perplexity", 0)),
        ("Google Search",       platforms.get("Google Search", 0)),
        ("Bing Copilot",        platforms.get("Bing Copilot", 0)),
        ("Google Gemini",       platforms.get("Google Gemini", 0)),
    ]

    # Two-column layout
    col1_x, col2_x = 18*mm, W/2 + 5*mm
    card_w = W/2 - 28*mm
    card_h = 28

    for i, (plat, sc) in enumerate(platforms_list):
        cx = col1_x if i % 2 == 0 else col2_x
        cy = y - (i // 2) * (card_h + 6)
        draw_rect(c, cx, cy, card_w, card_h, fill=WHITE, stroke=BORDER, radius=5, lw=0.6)

        # Platform name
        c.saveState()
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(TEXT_DARK)
        c.drawString(cx + 8, cy + 17, plat)
        c.restoreState()

        # Score bar
        bar_mini(c, cx + 8, cy + 9, sc, bar_w=card_w - 70, bar_h=5)
        c.saveState()
        c.setFont("Helvetica-Bold", 9)
        col_s = ACCENT if sc >= 70 else GOLD
        c.setFillColor(col_s)
        c.drawString(cx + card_w - 58, cy + 7, f"{sc}/100")
        c.restoreState()
        status = get_score_label(sc)
        status_pill(c, cx + card_w - 58, cy + 16, status, w=50, h=12)

    # ── GEO IMPRESSION SCORE ────────────────────────────────────────────────
    if impression_score > 0:
        y -= 10
        y = section_header(c, y, "GEO Impression Score", "Measured visibility in LLM-generated answers")
        y -= 14

        # Score card
        card_w = W - 36*mm
        card_h = 58  # Increased height for 3 metrics with proper spacing
        draw_rect(c, 18*mm, y - card_h, card_w, card_h, fill=WHITE, stroke=BORDER, radius=6, lw=0.6)
        y -= 10

        # Combined score
        c.saveState()
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(GREEN)
        c.drawString(24*mm, y - 20, f"{impression_score}")
        c.setFont("Helvetica", 14)
        c.setFillColor(TEXT_MID)
        c.drawString(24*mm + 35, y - 12, "/100")
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(TEXT_DARK)
        c.drawString(24*mm + 70, y - 10, "Combined Impression Score")
        c.restoreState()

        # Metrics - each metric on its own row
        metrics_x = 110*mm
        row_h = 14  # Height per row
        c.saveState()
        # Row 1: Position Score
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(TEXT_DARK)
        c.drawString(metrics_x, y, "Position Score:")
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MID)
        c.drawString(metrics_x + 38, y, f"{int(impression_position * 100)}/100")
        # Row 2: Word Count Score
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(TEXT_DARK)
        c.drawString(metrics_x, y - row_h, "Word Count Score:")
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MID)
        c.drawString(metrics_x + 38, y - row_h, f"{int(impression_word_count * 100)}/100")
        # Row 3: Citations
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(TEXT_DARK)
        c.drawString(metrics_x, y - row_h * 2, "Citations:")
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MID)
        c.drawString(metrics_x + 38, y - row_h * 2, f"{citation_count}")
        c.restoreState()

        y -= 66

        # Recommendations
        if impression_recommendations:
            y -= 6
            c.saveState()
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(TEXT_DARK)
            c.drawString(18*mm, y, "Recommendations:")
            c.restoreState()
            y -= 14
            for rec in impression_recommendations[:2]:
                c.saveState()
                c.setFont("Helvetica", 7.5)
                c.setFillColor(TEXT_MID)
                c.drawString(22*mm, y, f"• {rec[:80]}")
                c.restoreState()
                y -= 12

    page_footer(c, 2, 5, url, brand_name)
    c.showPage()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — CRAWLER ACCESS & BRAND AUTHORITY
# ══════════════════════════════════════════════════════════════════════════════

def draw_page3(c, data):
    url = data.get("url", "")
    brand_name = data.get("brand_name", "")
    crawlers = data.get("crawlers", [])
    crawler_access = data.get("crawler_access", {})
    international_platforms = data.get("international_platforms", {})
    cn_platforms = data.get("cn_platforms", {})

    y = H - 20*mm

    # Page header strip
    draw_rect(c, 0, H - 14*mm, W, 14*mm, fill=NAVY)
    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(18*mm, H - 9*mm, "Crawler Access & Brand Authority")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#A0B4C8"))
    c.drawRightString(W - 18*mm, H - 9*mm, f"{brand_name} · {url}")
    c.restoreState()

    y = H - 26*mm

    # ── AI CRAWLER ACCESS ─────────────────────────────────────────────────────
    y = section_header(c, y, "AI Crawler Access Status", "Blocking crawlers prevents AI citation")
    y -= 14

    # Build crawler data from crawler_access
    crawler_checks = []
    if crawler_access:
        robots_txt = crawler_access.get("robots_txt_ai_crawlers", {})
        if robots_txt:
            crawler_checks.append(("robots_txt_ai_crawlers", robots_txt.get("platform", ""), robots_txt.get("status", ""), "✓" if "Allowed" in str(robots_txt.get("status", "")) else "!", GREEN if "Allowed" in str(robots_txt.get("status", "")) else ORANGE))

        llms = crawler_access.get("llms_txt", {})
        if llms:
            crawler_checks.append(("llms_txt", llms.get("platform", ""), llms.get("status", ""), "✓" if llms.get("status") == "HTTP 200" else "!", GREEN if llms.get("status") == "HTTP 200" else ORANGE))

        geo = crawler_access.get("geo_blocking", {})
        if geo:
            crawler_checks.append(("geo_blocking", geo.get("platform", ""), geo.get("status", ""), "!" if "Restricted" in str(geo.get("status", "")) else "✓", ORANGE if "Restricted" in str(geo.get("status", "")) else GREEN))

    # Also add from crawlers list if present
    for crawler in crawlers[:6]:
        name = crawler.get("name", "")
        allowed = crawler.get("allowed", False)
        if name not in [c[0] for c in crawler_checks]:
            crawler_checks.append((name, "AI Crawler", "Allowed" if allowed else "Blocked", "✓" if allowed else "!", GREEN if allowed else RED_SOFT))

    if not crawler_checks:
        crawler_checks = [
            ("robots_txt_ai_crawlers", "All AI crawlers permitted", "Allowed", "✓", GREEN),
            ("llms_txt", "Comprehensive content", "HTTP 200", "✓", GREEN),
            ("geo_blocking", "Site accessibility", "Check needed", "!", ORANGE),
        ]

    draw_rect(c, 18*mm, y - 2, W - 36*mm, 16, fill=DARK_BLUE, radius=3)
    c.saveState()
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(WHITE)
    c.drawString(22*mm, y + 4, "Crawler / Check")
    c.drawString(85*mm, y + 4, "Details")
    c.drawString(W - 55*mm, y + 4, "Status")
    c.restoreState()
    y -= 18

    for idx, (crawler, detail, status, icon, col) in enumerate(crawler_checks):
        row_bg = LIGHT_BG if idx % 2 == 0 else WHITE
        draw_rect(c, 18*mm, y - 2, W - 36*mm, 22, fill=row_bg)

        # Icon circle
        c.saveState()
        c.setFillColor(col)
        c.circle(25*mm, y + 9, 6, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(WHITE)
        c.drawCentredString(25*mm, y + 6, icon)
        c.restoreState()

        c.saveState()
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(TEXT_DARK)
        # Friendly name mapping for crawler keys
        friendly_names = {
            "robots_txt_ai_crawlers": "AI Crawlers in robots.txt",
            "llms_txt": "llms.txt File",
            "geo_blocking": "Geo-blocking",
        }
        display_name = friendly_names.get(crawler, crawler.replace("_", " ").title())
        c.drawString(31*mm, y + 11, display_name)
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MID)
        c.drawString(31*mm, y + 2, str(detail)[:50])

        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(col)
        c.drawString(W - 53*mm, y + 6, str(status))
        c.restoreState()
        y -= 24

    y -= 10

    # ── BRAND AUTHORITY — INTERNATIONAL ───────────────────────────────────────
    y = section_header(c, y, "Brand Authority Signals", "International platform presence")
    y -= 14

    # Platform data
    platforms_data = [
        ("Twitter",   "Twitter", international_platforms.get("Twitter", {}).get("handle", ""), international_platforms.get("Twitter", {}).get("present", False)),
        ("Facebook",  "Facebook", international_platforms.get("Facebook", {}).get("handle", ""), international_platforms.get("Facebook", {}).get("present", False)),
        ("LinkedIn",  "LinkedIn", international_platforms.get("LinkedIn", {}).get("handle", ""), international_platforms.get("LinkedIn", {}).get("present", False)),
        ("Medium",    "Medium", international_platforms.get("Medium", {}).get("handle", ""), international_platforms.get("Medium", {}).get("present", False)),
        ("Reddit",    "Reddit", international_platforms.get("Reddit", {}).get("handle", ""), international_platforms.get("Reddit", {}).get("present", False)),
        ("YouTube",   "YouTube", international_platforms.get("YouTube", {}).get("handle", ""), international_platforms.get("YouTube", {}).get("present", False)),
        ("GitHub",    "GitHub", international_platforms.get("GitHub", {}).get("handle", ""), international_platforms.get("GitHub", {}).get("present", False)),
        ("Discord",   "Discord", international_platforms.get("Discord", {}).get("handle", ""), international_platforms.get("Discord", {}).get("present", False)),
        ("Telegram",  "Telegram", international_platforms.get("Telegram", {}).get("handle", ""), international_platforms.get("Telegram", {}).get("present", False)),
    ]

    draw_rect(c, 18*mm, y - 2, W - 36*mm, 16, fill=DARK_BLUE, radius=3)
    c.saveState()
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(WHITE)
    c.drawString(22*mm, y + 4, "Platform")
    c.drawString(65*mm, y + 4, "Handle / URL")
    c.drawRightString(W - 20*mm, y + 4, "Status")
    c.restoreState()
    y -= 16

    for idx, (plat, _, handle, present) in enumerate(platforms_data):
        row_bg = LIGHT_BG if idx % 2 == 0 else WHITE
        draw_rect(c, 18*mm, y - 3, W - 36*mm, 18, fill=row_bg)
        c.saveState()
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(TEXT_DARK)
        c.drawString(22*mm, y + 4, plat)
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MID)
        display_handle = handle if len(handle) <= 35 else handle[:32] + "..."
        c.drawString(65*mm, y + 4, display_handle)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(GREEN)
        status_text = "✓  Present" if present else "✗  Missing"
        c.drawRightString(W - 20*mm, y + 4, status_text)
        c.restoreState()
        y -= 18

    # Chinese media platforms (cn_media=true)
    if cn_platforms:
        y -= 6
        draw_rect(c, 18*mm, y - 2, W - 36*mm, 16, fill=DARK_BLUE, radius=3)
        c.saveState()
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(WHITE)
        c.drawString(22*mm, y + 4, "Platform")
        c.drawString(65*mm, y + 4, "Handle / URL")
        c.drawRightString(W - 20*mm, y + 4, "Status")
        c.restoreState()
        y -= 16

        cn_platforms_data = [
            ("WeChat",  cn_platforms.get("WeChat", {}).get("handle", ""), cn_platforms.get("WeChat", {}).get("present", False)),
            ("Weibo",   cn_platforms.get("Weibo", {}).get("handle", ""), cn_platforms.get("Weibo", {}).get("present", False)),
            ("Zhihu",   cn_platforms.get("Zhihu", {}).get("handle", ""), cn_platforms.get("Zhihu", {}).get("present", False)),
            ("Bilibili", cn_platforms.get("Bilibili", {}).get("handle", ""), cn_platforms.get("Bilibili", {}).get("present", False)),
            ("Douyin",  cn_platforms.get("Douyin", {}).get("handle", ""), cn_platforms.get("Douyin", {}).get("present", False)),
            ("Baidu",   cn_platforms.get("Baidu", {}).get("handle", ""), cn_platforms.get("Baidu", {}).get("present", False)),
        ]

        font_reg, font_bold = get_font_for_text()

        for idx, (plat, handle, present) in enumerate(cn_platforms_data):
            row_bg = LIGHT_BG if idx % 2 == 0 else WHITE
            draw_rect(c, 18*mm, y - 3, W - 36*mm, 18, fill=row_bg)
            c.saveState()
            # Use CJK font for Chinese text
            c.setFont(font_bold, 8)
            c.setFillColor(TEXT_DARK)
            c.drawString(22*mm, y + 4, plat)
            c.setFont(font_reg, 8)
            c.setFillColor(TEXT_MID)
            display_handle = handle if len(handle) <= 35 else handle[:32] + "..."
            c.drawString(65*mm, y + 4, display_handle)
            c.setFont(font_bold, 8)
            c.setFillColor(GREEN)
            status_text = "Present" if present else "Missing"
            c.drawRightString(W - 20*mm, y + 4, status_text)
            c.restoreState()
            y -= 18

    page_footer(c, 3, 5, url, brand_name)
    c.showPage()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — KEY FINDINGS
# ══════════════════════════════════════════════════════════════════════════════

def draw_page4(c, data):
    url = data.get("url", "")
    brand_name = data.get("brand_name", "")
    findings = data.get("findings", [])

    y = H - 20*mm

    # Page header strip
    draw_rect(c, 0, H - 14*mm, W, 14*mm, fill=NAVY)
    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(18*mm, H - 9*mm, "Key Findings")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#A0B4C8"))
    c.drawRightString(W - 18*mm, H - 9*mm, f"{brand_name} · {url}")
    c.restoreState()

    y = H - 26*mm

    y = section_header(c, y, "Key Findings", "Prioritized issues impacting GEO performance")
    y -= 14

    # Severity mapping
    severity_colors = {
        "critical": RED_SOFT,
        "high": ORANGE,
        "medium": GOLD,
        "low": TEXT_LIGHT,
    }

    severity_map = {
        "critical": "CRITICAL",
        "high": "HIGH",
        "medium": "MEDIUM",
        "low": "LOW",
    }

    # Default findings if none provided
    if not findings:
        findings = [
            ("CRITICAL", "No Wikipedia Article",
             "Wikipedia absence is the #1 authority gap for ChatGPT and Gemini. "
             "AI models heavily rely on Wikipedia for entity verification.", RED_SOFT),
            ("HIGH", "No Author Attribution",
             "Missing Person schema and visible author bylines reduce E-E-A-T signals.", ORANGE),
            ("HIGH", "No Publication Dates",
             "datePublished and dateModified fields are absent throughout the site.", ORANGE),
        ]

    # Process findings
    processed_findings = []
    for finding in findings[:6]:  # Limit to 6 findings
        if isinstance(finding, dict):
            sev = finding.get("severity", "medium").upper()
            title = finding.get("title", "")
            desc = finding.get("description", "")
        else:
            sev = "MEDIUM"
            title = str(finding)
            desc = ""
        col = severity_colors.get(sev.lower(), GOLD)
        processed_findings.append((sev, title, desc, col))

    for sev, title, desc, col in processed_findings:
        card_h = 58
        draw_rect(c, 18*mm, y - card_h + 8, W - 36*mm, card_h, fill=WHITE, stroke=BORDER, radius=6, lw=0.6)
        # Left accent bar
        draw_rect(c, 18*mm, y - card_h + 8, 4, card_h, fill=col, radius=3)

        # Severity badge
        badge_w = 55
        draw_rect(c, 24*mm, y - 4, badge_w, 15, fill=col, radius=4)
        c.saveState()
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(WHITE)
        c.drawCentredString(24*mm + badge_w/2, y + 1.5, sev)
        c.restoreState()

        # Title
        c.saveState()
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(TEXT_DARK)
        c.drawString(86*mm, y, title)
        c.restoreState()

        # Description (word wrap)
        max_w = W - 36*mm - 16*mm
        lines = word_wrap_text(c, desc, max_w, "Helvetica", 8)

        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MID)
        ly = y - 14
        for ln in lines[:3]:
            c.drawString(24*mm, ly, ln)
            ly -= 11
        c.restoreState()

        y -= card_h + 8

    page_footer(c, 4, 5, url, brand_name)
    c.showPage()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — ACTION PLAN & METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════

def draw_page5(c, data):
    url = data.get("url", "")
    brand_name = data.get("brand_name", "")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    quick_wins = data.get("quick_wins", [])
    medium_term = data.get("medium_term", [])
    strategic = data.get("strategic", [])

    # AutoGEO rules integration - merge with existing action items
    if HAS_AUTOGEO_RULES:
        business_type = data.get("business_type", "other")
        rules = get_rules_for_audit(business_type, "gemini")
        autogeo_plan = rules_to_action_plan(rules)

        # Merge AutoGEO rules into quick_wins (deduplicate)
        existing_qw = set()
        merged_qw = []
        for item in quick_wins:
            text = get_action_text(item)
            existing_qw.add(text)
            merged_qw.append(item)
        if autogeo_plan.get("quick_wins"):
            for action in autogeo_plan["quick_wins"]:
                rule = action.get("rule", "")
                if rule and rule not in existing_qw:
                    merged_qw.append(action)
                    existing_qw.add(rule)
        quick_wins = merged_qw

        # Merge AutoGEO rules into medium_term (deduplicate)
        existing_mt = set()
        merged_mt = []
        for item in medium_term:
            text = get_action_text(item)
            existing_mt.add(text)
            merged_mt.append(item)
        if autogeo_plan.get("medium_term"):
            for action in autogeo_plan["medium_term"]:
                rule = action.get("rule", "")
                if rule and rule not in existing_mt:
                    merged_mt.append(action)
                    existing_mt.add(rule)
        medium_term = merged_mt

    # Format date
    if "-" in date:
        try:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y")
        except:
            formatted_date = date
    else:
        formatted_date = date

    y = H - 20*mm

    # Page header strip
    draw_rect(c, 0, H - 14*mm, W, 14*mm, fill=NAVY)
    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(18*mm, H - 9*mm, "Action Plan & Methodology")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#A0B4C8"))
    c.drawRightString(W - 18*mm, H - 9*mm, f"{brand_name} · {url}")
    c.restoreState()

    y = H - 26*mm
    y = section_header(c, y, "Prioritized Action Plan", "Sequenced by impact and implementation effort")
    y -= 14

    # Default items if none provided
    if not quick_wins:
        quick_wins = ["Create Wikipedia article for brand", "Add Person schema for authors", "Add publication dates"]
    if not medium_term:
        medium_term = ["Add Wikipedia to sameAs properties", "Expand homepage content", "Implement security headers"]
    if not strategic:
        strategic = ["Build comprehensive Wikipedia presence", "Develop GEO content strategy", "Build E-E-A-T signals"]

    phases = [
        ("Quick Wins", "This Week", "High impact, low effort — implement immediately", ACCENT, quick_wins[:10]),
        ("Medium-Term", "This Month", "Significant impact, moderate effort", GOLD, medium_term[:10]),
        ("Strategic", "This Quarter", "Long-term competitive advantage — ongoing investment", GREEN, strategic[:5]),
    ]

    for phase, timeline, subtitle, col, items in phases:
        # Phase header
        draw_rect(c, 18*mm, y - 2, W - 36*mm, 20, fill=col, radius=5)
        c.saveState()
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(WHITE)
        c.drawString(22*mm, y + 6, phase)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#CCDDEE") if col == NAVY else WHITE)
        c.drawString(70*mm, y + 6, f"— {subtitle}")
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(WHITE)
        draw_rect(c, W - 52*mm, y + 2, 32*mm, 14, fill=colors.HexColor("#00000030"), radius=4)
        c.drawCentredString(W - 36*mm, y + 6, timeline)
        c.restoreState()
        y -= 22

        for i, item in enumerate(items):
            # Number bubble
            c.saveState()
            c.setFillColor(col)
            c.circle(23*mm, y + 6, 7, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(WHITE)
            c.drawCentredString(23*mm, y + 3, str(i + 1))
            c.restoreState()

            # Item text
            item_text = get_action_text(item)
            c.saveState()
            c.setFont("Helvetica", 9)
            c.setFillColor(TEXT_DARK)
            c.drawString(30*mm, y + 3, str(item_text))
            c.restoreState()

            # Divider
            if i < len(items) - 1:
                c.saveState()
                c.setStrokeColor(BORDER)
                c.setLineWidth(0.4)
                c.line(27*mm, y - 3, W - 18*mm, y - 3)
                c.restoreState()
            y -= 18

        y -= 10

    # ── METHODOLOGY BOX ───────────────────────────────────────────────────────
    y -= 4
    draw_rect(c, 18*mm, y - 42, W - 36*mm, 46, fill=LIGHT_BG, radius=6, stroke=BORDER, lw=0.6)

    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NAVY)
    c.drawString(22*mm, y - 4, "Methodology & Standards")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TEXT_MID)
    method_lines = [
        f"Audit Date: {formatted_date}  ·  Target: {url}",
        "Platforms: Google AI Overviews, ChatGPT Web Search, Perplexity AI, Google Gemini, Bing Copilot",
        "Standards: Google Search Quality Rater Guidelines, Schema.org, Core Web Vitals,",
        "           llms.txt emerging standard, RSL 1.0 licensing framework",
    ]
    my = y - 16
    for ln in method_lines:
        c.drawString(22*mm, my, ln)
        my -= 10
    c.restoreState()

    # Disclaimer
    y -= 56
    c.saveState()
    c.setFont("Helvetica", 6.5)
    c.setFillColor(TEXT_LIGHT)
    disclaimer = "This report was generated by the GEO-SEO Claude Code Analysis Tool. Scores and recommendations are based on automated analysis and industry benchmarks. Results should be validated with platform-specific testing."
    c.drawString(18*mm, y, disclaimer)
    c.restoreState()

    page_footer(c, 5, 5, url, brand_name)
    c.showPage()

# ══════════════════════════════════════════════════════════════════════════════
# BUILD
# ══════════════════════════════════════════════════════════════════════════════

def generate_report(data, output_path="GEO-REPORT.pdf"):
    """Generate the full PDF report from data dict."""
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(f"GEO Analysis Report — {data.get('brand_name', 'Website')}")
    c.setAuthor("GEO-SEO Claude Code Analysis Tool")
    c.setSubject("Generative Engine Optimization Audit")

    draw_cover(c, data)
    draw_page2(c, data)
    draw_page3(c, data)
    draw_page4(c, data)
    draw_page5(c, data)

    c.save()
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf_report.py <json_data_file> [output_file.pdf] [--dir path]")
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
        output_file = "GEO-REPORT.pdf"

    # Add timestamp if not already present
    if "GEO-REPORT.pdf" in output_file and "20" not in output_file[:20]:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = output_file.replace(".pdf", f"-{ts}.pdf")

    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.basename(output_file))

    result = generate_report(data, output_file)
    print(f"Report generated: {result}")