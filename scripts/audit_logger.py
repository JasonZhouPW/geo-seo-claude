#!/usr/bin/env python3
"""
Audit Logger — Generates detailed .log files for each GEO audit check item.
Format: 检查项目 | 子项目 | 该检查项目的说明 | 得分 | 实际情况 | 错误消息
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class AuditLogger:
    """Generates detailed audit log files in structured format."""

    def __init__(self, domain: str, output_dir: str = "."):
        self.domain = domain
        self.output_dir = Path(output_dir)
        self.entries: List[Dict[str, Any]] = []
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    def log(
        self,
        category: str,
        sub_item: str,
        description: str,
        score: Any,
        actual: str,
        error_message: Optional[str] = None,
        details: Optional[str] = None
    ):
        """Add a log entry."""
        self.entries.append({
            "category": category,
            "sub_item": sub_item,
            "description": description,
            "score": score,
            "actual": actual,
            "error_message": error_message,
            "details": details
        })

    def save(self, filename: Optional[str] = None) -> str:
        """Save log entries to .log file. Returns the filepath."""
        if filename is None:
            filename = f"audit-{self.timestamp}.log"
        filepath = self.output_dir / filename

        lines = []
        # Header
        lines.append(f"# GEO Audit Log — {self.domain}")
        lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# Total Entries: {len(self.entries)}")
        lines.append("")
        lines.append("Category,Sub-Item,Description,Score,Actual Status,Error Message")
        lines.append("-" * 120)

        for e in self.entries:
            actual = e["actual"]
            error = e.get("error_message") or ""
            details = e.get("details") or ""
            # Append details to description if present
            desc = e["description"]
            if details:
                desc = f"{desc} | Details: {details}"
            # Escape fields that contain commas
            def escape(val):
                if ',' in str(val) or '"' in str(val):
                    return f'"{str(val).replace('"', '""')}"'
                return val
            lines.append(
                f"{escape(e['category'])},{escape(e['sub_item'])},{escape(desc)},{e['score']},{escape(actual)},{escape(error)}"
            )

        filepath.write_text("\n".join(lines), encoding="utf-8")
        return str(filepath)

    def save_json(self, filename: Optional[str] = None) -> str:
        """Save log entries as structured JSON for programmatic use."""
        if filename is None:
            filename = f"audit-{self.timestamp}.json"
        filepath = self.output_dir / filename
        filepath.write_text(
            json.dumps({
                "domain": self.domain,
                "generated": datetime.now().isoformat(),
                "total_entries": len(self.entries),
                "entries": self.entries
            }, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return str(filepath)


def build_audit_logger_from_data(audit_data: Dict[str, Any], output_dir: str = ".") -> AuditLogger:
    """Build a detailed AuditLogger from audit-data.json."""
    domain = audit_data.get("url", "unknown").replace("https://", "").replace("http://", "")
    logger = AuditLogger(domain, output_dir)

    scores = audit_data.get("scores", {})
    crawler_access = audit_data.get("crawler_access", {})
    platforms = audit_data.get("platforms", {})
    findings = audit_data.get("findings", [])
    strengths = audit_data.get("strengths", [])
    schema_findings = audit_data.get("schema_findings", {})
    intl_platforms = audit_data.get("international_platforms", {})
    content_findings = audit_data.get("content_findings", {})

    # 1. AI Citability & Visibility
    cit_score = scores.get("ai_citability", 0)
    logger.log(
        "AI Citability & Visibility",
        "robots.txt",
        "Check AI crawler access permissions in robots.txt",
        cit_score,
        "good" if crawler_access.get("robots_txt_status") == "excellent" else "poor"
    )
    logger.log(
        "AI Citability & Visibility",
        "llms.txt",
        "Check if llms.txt exists and is well-structured",
        cit_score,
        "present" if crawler_access.get("llms_txt_present") else "missing"
    )
    logger.log(
        "AI Citability & Visibility",
        "GPTBot",
        "GPTBot crawler access permission",
        cit_score,
        crawler_access.get("ai_crawlers", {}).get("GPTBot", "unknown")
    )
    logger.log(
        "AI Citability & Visibility",
        "ClaudeBot",
        "ClaudeBot crawler access permission",
        cit_score,
        crawler_access.get("ai_crawlers", {}).get("ClaudeBot", "unknown")
    )
    logger.log(
        "AI Citability & Visibility",
        "PerplexityBot",
        "PerplexityBot crawler access permission",
        cit_score,
        crawler_access.get("ai_crawlers", {}).get("PerplexityBot", "unknown")
    )

    # 2. Brand Authority Signals
    brand_score = scores.get("brand_authority", 0)
    for platform, data in intl_platforms.items():
        presence = data.get("present", False) if isinstance(data, dict) else False
        logger.log(
            "Brand Authority Signals",
            platform,
            f"{platform} brand mention presence check",
            brand_score,
            "present" if presence else "missing"
        )

    # Wikipedia check (critical) — only add once
    wiki_logged = False
    for f in findings:
        if "wikipedia" in f.get("issue", "").lower() and not wiki_logged:
            logger.log(
                "Brand Authority Signals",
                "Wikipedia",
                "Wikipedia article existence — Critical signal for AI entity recognition",
                brand_score,
                "missing",
                error_message=f.get("detail", "")
            )
            wiki_logged = True

    # 3. Content Quality & E-E-A-T
    content_score = scores.get("content_eeat", 0)
    content_finding = content_findings or {}
    logger.log(
        "Content Quality & E-E-A-T",
        "Word Count",
        "Homepage content word count",
        content_score,
        content_finding.get("word_count", "N/A")
    )
    logger.log(
        "Content Quality & E-E-A-T",
        "Readability",
        "Content readability score (Flesch)",
        content_score,
        content_finding.get("readability", "N/A")
    )
    logger.log(
        "Content Quality & E-E-A-T",
        "E-E-A-T Score",
        "Experience, Expertise, Authoritativeness, Trustworthiness composite score",
        content_score,
        content_finding.get("eeat_score", "N/A")
    )

    # Author signals check
    has_author = any("author" in f.get("issue", "").lower() for f in findings)
    logger.log(
        "Content Quality & E-E-A-T",
        "Author Bylines",
        "Check if page includes author byline information",
        content_score,
        "missing" if has_author else "present"
    )

    # 4. Technical Foundations
    tech_score = scores.get("technical", 0)
    logger.log(
        "Technical Foundations",
        "HTTPS",
        "HTTPS encryption connection check",
        tech_score,
        "enabled"
    )
    logger.log(
        "Technical Foundations",
        "Rendering",
        "Page rendering method (SSR vs CSR)",
        tech_score,
        content_finding.get("rendering", "N/A")
    )
    logger.log(
        "Technical Foundations",
        "hreflang",
        "Multi-language hreflang tag implementation check",
        tech_score,
        "present"
    )
    logger.log(
        "Technical Foundations",
        "Meta Robots",
        "Check if Meta Robots tag exists",
        tech_score,
        "missing" if any("meta robots" in f.get("issue", "").lower() for f in findings) else "present"
    )

    # 5. Structured Data
    schema_score = scores.get("schema", 0)
    found_schemas = schema_findings.get("found_schemas", [])
    if isinstance(found_schemas, list):
        for schema_type in found_schemas:
            if isinstance(schema_type, str):
                logger.log(
                    "Structured Data",
                    schema_type,
                    f"Schema.org type {schema_type} presence check",
                    schema_score,
                    "present"
                )
            elif isinstance(schema_type, dict):
                logger.log(
                    "Structured Data",
                    schema_type.get("type", "Unknown"),
                    f"Schema.org type {schema_type.get('type','Unknown')} presence check",
                    schema_score,
                    "present" if schema_type.get("complete") else "incomplete"
                )

    missing_schemas = schema_findings.get("missing_opportunities", [])
    if isinstance(missing_schemas, list):
        for missing in missing_schemas:
            logger.log(
                "Structured Data",
                missing,
                f"Missing Schema.org type: {missing}",
                schema_score,
                "missing"
            )

    validation_errors = schema_findings.get("validation_errors", [])
    if isinstance(validation_errors, list):
        for err in validation_errors:
            logger.log(
                "Structured Data",
                "Validation Error",
                f"Schema validation error: {err}",
                schema_score,
                "error",
                error_message=err
            )

    # 6. Platform Optimization
    platform_score = scores.get("platform_optimization", 0)
    if isinstance(platforms, dict):
        for platform_name, score_val in platforms.items():
            status = "good" if isinstance(score_val, (int, float)) and score_val >= 60 else "poor"
            if isinstance(score_val, dict):
                score_val = score_val.get("score", 0)
            logger.log(
                "Platform Optimization",
                platform_name,
                f"{platform_name} platform readiness score",
                score_val,
                status
            )

    # Findings summary
    for f in findings:
        logger.log(
            "Findings Summary",
            f.get("category", "unknown"),
            f.get("issue", ""),
            "N/A",
            f.get("severity", "unknown"),
            error_message=f.get("detail", "")
        )

    # Strengths summary
    for s in strengths:
        logger.log(
            "Strengths Summary",
            "Positive Signal",
            s,
            "N/A",
            "pass"
        )

    return logger


def generate_audit_log(audit_data_path: str, output_dir: str) -> str:
    """Generate audit log file from audit-data.json. Returns the log filepath."""
    with open(audit_data_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    logger = build_audit_logger_from_data(audit_data, output_dir)
    log_path = logger.save()
    json_path = logger.save_json()
    return log_path, json_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python audit_logger.py <audit-data.json> [output_dir]")
        sys.exit(1)

    audit_json = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    log_path, json_path = generate_audit_log(audit_json, out_dir)
    print(f"Log saved to: {log_path}")
    print(f"JSON log saved to: {json_path}")
