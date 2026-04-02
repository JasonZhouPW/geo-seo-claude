# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **GEO (Generative Engine Optimization) + SEO analysis toolkit** delivered as a Claude Code Skill. It optimizes websites for AI-powered search engines (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews) while maintaining traditional SEO foundations. MIT licensed.

## Commands

Run via `/geo` prefix in Claude Code:

| Command | Description |
|---------|-------------|
| `/geo audit <url>` | Full GEO + SEO audit with parallel subagents |
| `/geo page <url>` | Deep single-page GEO analysis |
| `/geo quick <url>` | 60-second GEO visibility snapshot |
| `/geo citability <url>` | Score content for AI citation readiness |
| `/geo crawlers <url>` | Check AI crawler access (robots.txt) |
| `/geo llmstxt <url>` | Analyze or generate llms.txt |
| `/geo brands <url>` | Scan brand mentions across AI-cited platforms |
| `/geo platforms <url>` | Platform-specific optimization |
| `/geo schema <url>` | Structured data analysis & generation |
| `/geo technical <url>` | Technical SEO audit |
| `/geo content <url>` | Content quality & E-E-A-T assessment |
| `/geo report <url>` | Generate client-ready GEO report |
| `/geo report-pdf <url>` | Generate professional PDF report with charts |
| `/geo prospect <cmd>` | CRM-lite prospect pipeline management |
| `/geo proposal <domain>` | Auto-generate client proposals |
| `/geo compare <domain>` | Monthly delta tracking & progress reports |

## Architecture

**Orchestration Pattern:**
- `geo/SKILL.md` is the main entry point/router - dispatches to subagents and sub-skills
- **5 parallel subagents** run simultaneously during full audits:
  - `geo-ai-visibility` - citability, crawlers, llms.txt, brand mentions
  - `geo-platform-analysis` - ChatGPT, Perplexity, Google AIO readiness
  - `geo-technical` - Core Web Vitals, SSR, crawlability, mobile, security
  - `geo-content` - E-E-A-T, readability, AI content detection
  - `geo-schema` - JSON-LD detection, validation, generation
- **13 sub-skills** in `skills/` provide specialized capabilities
- **Python scripts** in `scripts/` handle heavy lifting (fetching, scoring, PDF generation)

**Composite GEO Score Weights:**
- AI Citability & Visibility: 25%
- Brand Authority Signals: 20%
- Content Quality & E-E-A-T: 20%
- Technical Foundations: 15%
- Structured Data: 10%
- Platform Optimization: 10%

## Testing

```bash
python3 -m pytest tests/
```

## Key Technical Notes

- **SSR detection is critical** - AI crawlers generally do NOT execute JavaScript, so client-side rendered content is invisible to them. The `fetch_page.py` script (not WebFetch) is used for schema detection because WebFetch strips `<head>` content.
- **Wikipedia API** for brand mention verification uses direct Python requests (not web search).
- **PDF generation** uses ReportLab - no external PDF service dependency.
- **CRM/prospect data** stored at `~/.geo-prospects/` (outside this repo).

## Development Workflow

**重要：所有开发修改必须在项目目录下进行，然后同步到 `~/.claude/skills/geo/`，不要直接编辑 `~/.claude` 目录下的文件。**

1. **修改文件**：所有代码、脚本、SKILL.md 等都在 `/Users/jasonzhou/work/other/geo-seo-claude/` 下
2. **同步部署**：`install.sh` 或手动复制到 `~/.claude/skills/geo/`
3. **禁止直接编辑**：不直接修改 `~/.claude/skills/geo/` 下的文件（仅供验证同步结果用）

**目录对应关系：**
```
geo-seo-claude/           →  ~/.claude/skills/geo/
├── geo/SKILL.md          →  SKILL.md
├── skills/               →  skills/
├── agents/               →  agents/
└── scripts/              →  scripts/
```
