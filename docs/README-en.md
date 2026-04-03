# GEO-SEO Analysis Tool — User Guide

> **Philosophy:** GEO-first, SEO-supported. AI search is eating traditional search.
> This tool optimizes for where traffic is going, not where it was.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Understanding GEO Scores](#understanding-geo-scores)
- [Report Types](#report-types)
- [Examples](#examples)
- [Scoring Methodology](#scoring-methodology)
- [Business Type Detection](#business-type-detection)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Claude Code CLI (`/help` to install)
- Python 3.8+ for report generation scripts
- Git for cloning the repository
- Internet access for web scraping

### Option 1: Automated Installer (Recommended)

The easiest way to install is using the `install.sh` script:

```bash
# Download and run the installer
curl -sL https://raw.githubusercontent.com/zubair-trabzada/geo-seo-claude/main/install.sh | bash

# Or if you already have the repo locally
./install.sh
```

The installer will:
- Check prerequisites (Git, Python 3.8+, Claude Code)
- Create required directories
- Install main skill to `~/.claude/skills/geo/`
- Install 13 sub-skills to `~/.claude/skills/`
- Install 5 subagents to `~/.claude/agents/`
- Install utility scripts
- Install schema templates
- Install Python dependencies
- Optionally install Playwright for screenshots
- Verify installation

### Option 2: Manual Installation

1. **Clone or copy the repository** to your local machine.

2. **Run the installer**:

   ```bash
   ./install.sh
   ```

   This handles all file placement and dependency installation automatically.

3. **Or manually copy files**:

   ```bash
   # Create directories
   mkdir -p ~/.claude/skills/geo
   mkdir -p ~/.claude/agents

   # Copy skill files
   cp geo/* ~/.claude/skills/geo/
   cp -r skills/*/ ~/.claude/skills/
   cp agents/*.md ~/.claude/agents/
   cp scripts/* ~/.claude/skills/geo/scripts/
   ```

4. **Install Python dependencies**:

   ```bash
   pip install reportlab Pillow requests beautifulsoup4
   ```

### Verify Installation

After installation, verify it works:

```
/geo help
```

You should see the GEO-SEO tool help menu with all available commands.

---

## Quick Start

### 60-Second Snapshot

```bash
/geo quick https://example.com
```

### Full GEO Audit (5–10 minutes)

```bash
/geo audit https://example.com
```

### Full Audit with Action Plan

```bash
/geo audit https://example.com has-solution=true
```

---

## Command Reference

### `/geo audit <url> [has-solution] [cn-media]`

**Full GEO + SEO audit with parallel subagent delegation.**

Performs a comprehensive Generative Engine Optimization audit across AI citability, platform analysis, technical infrastructure, content quality, and schema markup.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | Target website URL |
| `has-solution` | boolean | `false` | Include prioritized action plan |
| `cn-media` | boolean | `true` | Include Chinese media platforms (WeChat, Weibo, Zhihu, etc.) |

**What it does:**

1. **Phase 1 — Discovery**: Fetches homepage, detects business type, crawls sitemap/internal links (max 50 pages)
2. **Phase 2 — Parallel Analysis**: Launches 5 subagents simultaneously:
   - `geo-ai-visibility` — Citability, crawlers, llms.txt, brand mentions
   - `geo-platform-analysis` — ChatGPT, Perplexity, Google AIO readiness
   - `geo-technical` — Core Web Vitals, SSR, crawlability, security
   - `geo-content` — E-E-A-T, readability, author signals
   - `geo-schema` — JSON-LD detection and validation
3. **Phase 3 — Synthesis**: Calculates composite GEO Score, generates JSON + MD + PDF reports

**Output files:**
- `audit-data.json` — Raw audit data
- `GEO-REPORT-{timestamp}.md` — Markdown report
- `GEO-REPORT-{timestamp}.pdf` — Professional PDF report

**Examples:**

```bash
# Basic audit (no action plan, includes Chinese media)
/geo audit https://bigmodel.cn

# Full audit with action plan
/geo audit https://bigmodel.cn has-solution=true

# Audit without Chinese media
/geo audit https://bigmodel.cn cn-media=false

# Full audit with action plan and Chinese media (explicit)
/geo audit https://bigmodel.cn has-solution=true cn-media=true
```

---

### `/geo page <url>`

**Deep single-page GEO analysis.**

Analyzes a single page in detail — content structure, schema markup, meta tags, heading hierarchy, and AI citability.

```bash
/geo page https://bigmodel.cn/pricing
```

---

### `/geo citability <url>`

**Score content for AI citation readiness.**

Evaluates how quotable and extractable your content is for AI systems. Factors:
- Sentence structure and clarity
- Presence of statistics and facts
- Answer block optimization
- Passage-level scoring

```bash
/geo citability https://bigmodel.cn/blog
```

---

### `/geo crawlers <url>`

**Check AI crawler access (robots.txt analysis).**

Analyzes whether AI systems can access your site:

| Crawler | Description |
|---------|-------------|
| GPTBot | OpenAI (ChatGPT) |
| Claude (ClaudeBot) | Anthropic |
| Google-Extended | Google (AI Overviews) |
| CCBot | Common Crawl |
| PerplexityBot | Perplexity |

```bash
/geo crawlers https://bigmodel.cn
```

---

### `/geo llmstxt <url>`

**Analyze or generate llms.txt file.**

The `llms.txt` is a new standard (created by Andrew Ng) that helps AI systems understand your site structure. This command:

1. Checks if `llms.txt` exists
2. Validates content-type header (must be `text/plain`)
3. Analyzes completeness and quality
4. Generates a template if missing

```bash
/geo llmstxt https://bigmodel.cn
```

---

### `/geo brands <url>`

**Scan brand mentions across AI-cited platforms.**

Scans for brand presence on platforms that AI models cite frequently:

**International Platforms:**
- Wikipedia
- LinkedIn
- YouTube
- GitHub
- Reddit

**Chinese Platforms** (when `cn-media=true`):
- WeChat
- Weibo
- Zhihu
- Bilibili
- Douyin

```bash
/geo brands https://bigmodel.cn
/geo brands https://bigmodel.cn cn-media=false
```

---

### `/geo platforms <url>`

**Platform-specific optimization analysis.**

Assesses readiness for major AI platforms:

| Platform | Description |
|----------|-------------|
| Google AI Overviews | Google's AI-powered search results |
| ChatGPT | OpenAI's conversational AI |
| Perplexity | AI-powered search engine |
| Google Gemini | Google's multimodal AI |
| Bing Copilot | Microsoft's AI assistant |

```bash
/geo platforms https://bigmodel.cn
```

---

### `/geo schema <url>`

**Detect, validate, and generate structured data.**

Analyzes Schema.org markup on your site and provides:
- JSON-LD detection and validation
- Missing schema type recommendations
- Generated schema templates

```bash
/geo schema https://bigmodel.cn
```

---

### `/geo technical <url>`

**Traditional technical SEO audit.**

Covers:
- Server-side rendering (SSR) detection
- Core Web Vitals readiness
- Crawlability and indexability
- HTTPS and security headers
- Mobile optimization
- hreflang tags

```bash
/geo technical https://bigmodel.cn
```

---

### `/geo content <url>`

**Content quality and E-E-A-T assessment.**

Evaluates:
- **Experience** — First-hand knowledge signals
- **Expertise** — Subject matter expertise
- **Authoritativeness** — Industry authority
- **Trustworthiness** — Credibility and reliability
- Author bios and credentials
- Content freshness and depth
- Source citations

```bash
/geo content https://bigmodel.cn
```

---

### `/geo report <url>`

**Generate client-ready GEO deliverable.**

Creates a presentation-ready markdown report with:
- Executive summary
- Score breakdown
- Key findings by severity
- Prioritized action plan

```bash
/geo report https://bigmodel.cn
```

---

### `/geo report-pdf <url>`

**Generate professional PDF report with charts and scores.**

Creates a branded PDF with:
- Cover page with GEO score gauge
- Score breakdown bar charts
- AI Platform Readiness dashboard
- Crawler Access status table
- Key findings by severity
- Prioritized action plan
- Methodology appendix

```bash
/geo report-pdf https://bigmodel.cn
```

---

### `/geo quick <url>`

**60-second GEO visibility snapshot.**

Fast inline analysis covering:
- Business type detection
- Top 3 strengths
- Top 3 issues
- Quick wins

```bash
/geo quick https://bigmodel.cn
```

---

### `/geo rewrite <url> [--engine gemini|gpt|claude] [--prompt-only]`

**Rewrite page content using AutoGEO rules for AI visibility.**

Generates a rewrite prompt that can be fed to an LLM to optimize content for AI citation.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--engine` | `gemini` | Target AI platform |
| `--prompt-only` | — | Output rewrite prompt without calling LLM |

```bash
# Generate rewrite prompt for Gemini
/geo rewrite https://bigmodel.cn

# Target GPT optimization
/geo rewrite https://bigmodel.cn --engine gpt

# View prompt only (don't execute)
/geo rewrite https://bigmodel.cn --prompt-only
```

---

### `/geo evaluate <url>`

**GEU (Generative Engine Utility) quality evaluation using LLM assessment.**

Evaluates rewritten content quality across 6 dimensions (Clarity, Depth, Balance, Breadth, Support, Insightfulness) and citation metrics.

**Requires:** API key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--provider` | `openai` | LLM provider (`openai`, `anthropic`, `claude`) |
| `--skip-rewrite` | — | Evaluate original content only |
| `--output` | — | Save results to JSON file |

```bash
# Full evaluation with rewrite
/geo evaluate https://bigmodel.cn

# Evaluate original content only
/geo evaluate https://bigmodel.cn --skip-rewrite

# Use Claude for evaluation
/geo evaluate https://bigmodel.cn --provider claude --output geu.json
```

**GEU Score Dimensions:**
- **Clarity** — Structure, logic flow, lack of redundancy
- **Depth** — Analytical depth, critical thinking
- **Balance** — Fairness, objectivity, multiple perspectives
- **Breadth** — Coverage of relevant subtopics
- **Support** — Claims substantiated with evidence
- **Insightfulness** — Originality, actionable recommendations

**Note:** This command requires LLM API access and may incur costs.

---

### `/geo prospect <cmd>`

**CRM-lite for managing prospects through the sales pipeline.**

Commands:

| Command | Description |
|---------|-------------|
| `list` | List all prospects |
| `add <domain> <stage>` | Add new prospect |
| `update <domain> <stage>` | Update prospect stage |
| `notes <domain> <notes>` | Add notes |

**Stages:** `lead` → `qualified` → `proposal` → `negotiation` → `won` → `lost`

```bash
/geo prospect list
/geo prospect add example.com lead
/geo prospect update example.com qualified
/geo prospect notes example.com "Scheduled demo for next week"
```

---

### `/geo proposal <domain>`

**Auto-generate client proposal from audit data.**

Creates a professional proposal document based on the latest audit for a domain.

```bash
/geo proposal bigmodel.cn
```

Output: `~/.geo-prospects/proposals/{domain}-proposal-{date}.md`

---

### `/geo compare <domain>`

**Monthly delta report — show score improvements to client.**

Compares the two most recent audits for a domain and shows:
- Score changes by category
- New issues found
- Issues resolved
- Progress summary

```bash
/geo compare bigmodel.cn
```

Output: `~/.geo-prospects/reports/{domain}-monthly-{YYYY-MM}.md`

---

## Understanding GEO Scores

### Score Ranges

| Range | Rating | Interpretation |
|-------|--------|----------------|
| 90–100 | Excellent | Top-tier GEO optimization; highly likely to be cited by AI |
| 75–89 | Good | Strong GEO foundation with room for improvement |
| 60–74 | Fair | Moderate GEO presence; significant optimization opportunities |
| 40–59 | Poor | Weak GEO signals; AI systems may struggle to cite |
| 0–39 | Critical | Minimal GEO optimization; largely invisible to AI systems |

### Score Categories

| Category | Weight | What It Measures |
|----------|--------|------------------|
| AI Citability | 25% | How quotable/extractable content is for AI systems |
| Brand Authority | 20% | Third-party mentions, entity recognition signals |
| Content E-E-A-T | 20% | Experience, Expertise, Authoritativeness, Trustworthiness |
| Technical GEO | 15% | AI crawler access, llms.txt, rendering, speed |
| Schema & Structured Data | 10% | Schema.org markup quality and completeness |
| Platform Optimization | 10% | Presence on platforms AI models cite |

**Note:** When measured, a **7th category — GEO Impression Score** — is included at 14% weight. This score assesses how well the site appears in LLM-generated answers based on citation frequency, position, and content length. When not measured, it shows 0% and is excluded from the formula.

**Formula (6-category, standard):**
```
GEO_Score = (Citability × 0.25) + (Brand × 0.20) + (EEAT × 0.20) + (Technical × 0.15) + (Schema × 0.10) + (Platform × 0.10)
```

**Formula (7-category, with GEO Impression Score):**
```
GEO_Score = (Citability × 0.22) + (Brand × 0.18) + (EEAT × 0.18) + (Technical × 0.12) + (Schema × 0.08) + (Platform × 0.08) + (Impression × 0.14)
```

### Issue Severity Classification

**Critical (Fix Immediately):**
- All AI crawlers blocked in robots.txt
- No indexable content (JavaScript-rendered only)
- Domain-level noindex directive
- Site returns 5xx errors on key pages
- Complete absence of structured data

**High (Fix Within 1 Week):**
- Key AI crawlers blocked
- No llms.txt file present
- Missing Organization schema
- No author attribution on content pages

**Medium (Fix Within 1 Month):**
- Partial AI crawler blocking
- llms.txt exists but incomplete
- Missing FAQ schema
- Thin author bios without credentials

**Low (Optimize When Possible):**
- Minor schema validation errors
- Some images missing alt text
- Missing Open Graph tags

---

## Report Types

### JSON Data (`audit-data.json`)

Raw audit data for programmatic use:
```json
{
  "url": "https://example.com",
  "brand_name": "Example",
  "date": "2026-04-02",
  "business_type": "saas",
  "geo_score": 75,
  "scores": {
    "ai_citability": 78,
    "brand_authority": 72,
    "content_eeat": 80,
    "technical": 75,
    "schema": 70,
    "platform_optimization": 68
  },
  "platforms": {...},
  "findings": [...],
  "quick_wins": [...],
  "medium_term": [...],
  "strategic": [...]
}
```

### Markdown Report (`GEO-REPORT-{timestamp}.md`)

Human-readable report with:
- Executive summary
- Score breakdown
- Detailed findings by category
- Action plan (when `has-solution=true`)

### PDF Report (`GEO-REPORT-{timestamp}.pdf`)

Professional client-ready report with:
- Cover page with GEO score gauge
- Color-coded score charts
- AI Platform Readiness dashboard
- Crawler Access status table
- Findings by severity
- Prioritized action plan
- Methodology appendix

---

## Examples

### Example 1: Initial Audit for a New Client

```bash
# 1. Quick snapshot to assess potential
/geo quick https://acme.com

# 2. Full audit with action plan
/geo audit https://acme.com has-solution=true cn-media=true

# 3. Generate PDF for client delivery
/geo report-pdf https://acme.com
```

### Example 2: Technical Deep Dive

```bash
# Check why AI might not be citing your content
/geo technical https://acme.com

# Verify crawler access
/geo crawlers https://acme.com

# Check llms.txt status
/geo llmstxt https://acme.com
```

### Example 3: Content Optimization

```bash
# Assess content quality
/geo content https://acme.com/blog

# Score specific pages for citability
/geo citability https://acme.com/blog/best-post

# Generate rewrite prompt
/geo rewrite https://acme.com/blog/best-post --engine gpt
```

### Example 4: Platform-Specific Strategy

```bash
# Check ChatGPT/Perplexity readiness
/geo platforms https://acme.com

# Scan brand mentions
/geo brands https://acme.com
```

### Example 5: Client Management

```bash
# Add new prospect
/geo prospect add acme.com lead

# After audit, generate proposal
/geo proposal acme.com

# Next month, show progress
/geo compare acme.com
```

---

## Scoring Methodology

### Business Type Detection

The tool automatically classifies websites into types:

| Type | Detection Signals |
|------|-------------------|
| **SaaS** | Pricing page, "Sign up", "Free trial", `/app` subdomain, feature tables |
| **Local Business** | Address, phone, Google Maps, "Near me", service area pages |
| **E-commerce** | Product pages, cart, "Add to cart", price displays, product schema |
| **Publisher** | Blog, articles, bylines, publication dates, article schema |
| **Agency** | Portfolio, case studies, "Our services", client logos, testimonials |

### Crawl Limits

- **Max 50 pages** per full audit
- **30-second timeout** per page fetch
- **1-second delay** between requests
- **Robots.txt** directives always respected

---

## Troubleshooting

### "llms.txt returns HTML instead of text"

This means your server is returning `Content-Type: text/html` instead of `Content-Type: text/plain`. Fix by configuring your web server to serve `llms.txt` with the correct content type.

### "AI Citability score is very low"

Common causes:
1. **Client-side rendering (SPA)** — AI crawlers only see the loading screen
2. **Thin content** — Not enough substantive text
3. **No statistics or facts** — AI prefers quotable data
4. **Poor heading structure** — Hard to parse into answer blocks

### "Brand Authority score is low"

AI models use third-party signals for entity recognition:
- Wikipedia presence (create/edit a Wikipedia page)
- YouTube channel with subscribers
- LinkedIn company page with employees
- Press mentions on authoritative sites
- Industry awards and certifications

### "Schema score is 0"

Your site likely has no JSON-LD structured data. Use:
```bash
/geo schema https://your-site.com
```
to get specific schema recommendations and templates.

### PDF generation fails

Install dependencies:
```bash
pip install reportlab Pillow requests beautifulsoup4
```

### Reports not generating

Check that all 5 subagents completed successfully. If Phase 2 failed, Phase 3 won't run. Re-run the audit:
```bash
/geo audit https://your-site.com has-solution=true
```

---

## Glossary

| Term | Definition |
|------|------------|
| **GEO** | Generative Engine Optimization — optimizing content for AI citation |
| **AI Citability** | How extractable and quotable content is for AI systems |
| **llms.txt** | A text file helping AI systems understand your site structure |
| **E-E-A-T** | Experience, Expertise, Authoritativeness, Trustworthiness |
| **Structured Data** | Schema.org markup helping search engines understand content |
| **AI Overviews** | Google's AI-powered search results (formerly SGE) |
| **Entity Recognition** | How AI systems identify and understand brands/concepts |
| **SSR** | Server-Side Rendering — content available before JavaScript executes |
| **CSR** | Client-Side Rendering — content only available after JavaScript runs |

---

## Support

For issues or feature requests, open an issue at:
https://github.com/your-repo/geo-seo-claude/issues
