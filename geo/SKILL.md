---
name: geo
description: >
  GEO-first SEO analysis tool. Optimizes websites for AI-powered search engines
  (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews) while maintaining
  traditional SEO foundations. Performs full GEO audits, citability scoring,
  AI crawler analysis, llms.txt generation, brand mention scanning, platform-specific
  optimization, schema markup, technical SEO, content quality (E-E-A-T), and
  client-ready GEO report generation. Use when user says "geo", "seo", "audit",
  "AI search", "AI visibility", "optimize", "citability", "llms.txt", "schema",
  "brand mentions", "GEO report", or any URL for analysis.
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO-SEO Analysis Tool — Claude Code Skill (February 2026)

> **Philosophy:** GEO-first, SEO-supported. AI search is eating traditional search.
> This tool optimizes for where traffic is going, not where it was.

---

## Quick Reference

| Command | What It Does |
|---------|-------------|
| `/geo audit <url> [has-solution] [cn-media] [use-proxy] [proxy_url]` | Full GEO + SEO audit with parallel subagents. `has-solution`: false=skip solutions (default), true=include action plan. `cn-media`: true=include Chinese media (default), false=exclude. `use-proxy`: false=direct access (default), true=use proxy. `proxy_url`: required when `use-proxy=true`, the proxy URL (e.g., `http://127.0.0.1:12377`) |
| `/geo page <url>` | Deep single-page GEO analysis |
| `/geo citability <url>` | Score content for AI citation readiness |
| `/geo crawlers <url>` | Check AI crawler access (robots.txt analysis) |
| `/geo llmstxt <url>` | Analyze or generate llms.txt file |
| `/geo brands <url>` | Scan brand mentions across AI-cited platforms |
| `/geo platforms <url>` | Platform-specific optimization (ChatGPT, Perplexity, Google AIO) |
| `/geo schema <url>` | Detect, validate, and generate structured data |
| `/geo technical <url>` | Traditional technical SEO audit |
| `/geo content <url>` | Content quality and E-E-A-T assessment |
| `/geo report <url>` | Generate client-ready GEO deliverable |
| `/geo report-pdf <url>` | Generate professional PDF report with charts and scores |
| `/geo quick <url>` | 60-second GEO visibility snapshot |
| `/geo prospect <cmd>` | CRM-lite: manage prospects through the sales pipeline |
| `/geo proposal <domain>` | Auto-generate client proposal from audit data |
| `/geo compare <domain>` | Monthly delta report: show score improvements to client |
| `/geo rewrite <url>` | Rewrite page content using AutoGEO rules for AI visibility |
| `/geo evaluate <url>` | GEU (Generative Engine Utility) quality evaluation using LLM assessment |
| `/geo impression <url>` | GEO Impression Score - measure citation visibility in LLM responses |

---

## `/geo evaluate` — GEU Quality Evaluation

Evaluate rewritten content quality using LLM-based assessment across 6 dimensions (Clarity, Depth, Balance, Breadth, Support, Insightfulness) and citation metrics.

**Usage:**
```
/geo evaluate <url> [--provider openai|anthropic|claude] [--skip-rewrite] [--output result.json]
```

**Parameters:**
- `url`: Target webpage URL
- `--provider`: LLM provider to use (default: `openai`)
- `--skip-rewrite`: Evaluate original content only (skip rewriting)
- `--output`: Save results to JSON file

**Examples:**
```
/geo evaluate https://example.com                    # Full evaluation with rewrite
/geo evaluate https://example.com --skip-rewrite     # Evaluate original only
/geo evaluate https://example.com --provider claude  # Use Claude for evaluation
/geo evaluate https://example.com --output geu.json  # Save results
```

**GEU Score Dimensions:**
| Dimension | Description |
|-----------|-------------|
| Clarity | Structure, logic flow, lack of redundancy |
| Depth | Analytical depth, critical thinking |
| Balance | Fairness, objectivity, multiple perspectives |
| Breadth | Coverage of relevant subtopics |
| Support | Claims substantiated with evidence |
| Insightfulness | Originality, actionable recommendations |

**Output:**
- `quality_dimensions` — 6 dimension scores (0.0-1.0)
- `citation_metrics` — claim extraction and citation recall
- `overall_quality_score` — weighted average

---

## `/geo impression` — GEO Impression Score

Measure how visible content is in LLM-generated answers based on citation position, frequency, and word count.

**Usage:**
```
/geo impression <url> [--provider openai|anthropic|claude] [--query "question"] [--output result.json]
```

**Parameters:**
- `url`: Target webpage URL
- `--provider`: LLM provider to use (default: `openai`)
- `--query`: Question to ask about the page (default: "What is this page about?")
- `--output`: Save results to JSON file

**Examples:**
```
/geo impression https://example.com                    # Basic impression score
/geo impression https://example.com --query "What products do they offer?"  # Custom query
/geo impression https://example.com --provider claude --output impression.json
```

**GEO Impression Score Dimensions:**
| Dimension | Description |
|-----------|-------------|
| Position Score | Earlier citations score higher (exponential decay) |
| Word Count Score | More substantive content with specific details scores higher |
| Combined Score | Weighted combination of position and word count |
| Citation Count | Number of times content is cited in the LLM response |

**Output:**
- `geo_impression_score` section in JSON with all metrics
- Saved to URL-based domain subfolder

---

## `/geo rewrite` — Document Rewriting

Rewrite webpage content to maximize visibility in LLM-generated answers, powered by AutoGEO rules (ICLR 2026).

**Usage:**
```
/geo rewrite <url> [--engine gemini|gpt|claude] [--prompt-only]
```

**Parameters:**
- `url`: Target webpage URL
- `--engine`: Target AI platform (default: `gemini`)
- `--prompt-only`: Output rewrite prompt without calling LLM

**Examples:**
```
/geo rewrite https://example.com                    # Generate rewrite prompt
/geo rewrite https://example.com --engine gpt     # Target GPT optimization
/geo rewrite https://example.com --prompt-only     # View prompt only
```

**How It Works:**
1. Fetch webpage content
2. Detect business type (SaaS, E-commerce)
3. Generate AutoGEO-style rewrite prompt with relevant rules
4. Return prompt for LLM rewriting

**Output:** Rewrite prompt file (`rewrite-prompt.md`)

---

## Market Context (Why GEO Matters)

| Metric | Value | Source |
|--------|-------|--------|
| GEO services market (2025) | $850M-$886M | Yahoo Finance / Superlines |
| Projected GEO market (2031) | $7.3B (34% CAGR) | Industry analysts |
| AI-referred sessions growth | +527% (Jan-May 2025) | SparkToro |
| AI traffic conversion vs organic | 4.4x higher | Industry data |
| Google AI Overviews reach | 1.5B users/month, 200+ countries | Google |
| ChatGPT weekly active users | 900M+ | OpenAI |
| Perplexity monthly queries | 500M+ | Perplexity |
| Gartner: search traffic drop by 2028 | -50% | Gartner |
| Marketers investing in GEO | Only 23% | Industry surveys |
| Brand mentions vs backlinks for AI | 3x stronger correlation | Ahrefs (Dec 2025) |

---

## Orchestration Logic

### Full Audit (`/geo audit <url> [has-solution] [cn-media] [use-proxy] [proxy_url]`)

**Parameters:**
- `url` (required): The website URL to audit
- `has-solution` (optional, default: `false`): When `false`, the report excludes the "Action Plan" / solutions section. When `true`, includes prioritized recommendations.
- `cn-media` (optional, default: `true`): When `true`, includes Chinese media platforms in brand mention scanning (WeChat, Weibo, Zhihu, Bilibili, Douyin, Baidu, etc.). When `false`, excludes Chinese media.
- `use-proxy` (optional, default: `false`): When `true`, enables proxy access for geo-blocked sites. Requires `proxy_url` to be set.
- `proxy_url` (optional, required when `use-proxy=true`): The proxy URL to use (e.g., `http://127.0.0.1:12377`). Must be non-empty when `use-proxy=true`.

**Phase 1: Discovery (Sequential)**
1. **If `use-proxy=true`**: Execute `export https_proxy="<proxy_url>"` before any fetching operations. If `proxy_url` is empty when `use-proxy=true`, abort with error.
1. Fetch homepage HTML (curl or WebFetch)
2. Detect business type (SaaS, Local, E-commerce, Publisher, Agency, Other)
3. Extract key pages from sitemap.xml or internal links (up to 50 pages)

**Phase 2: Parallel Analysis (Delegate to Subagents)**
Launch these 5 subagents simultaneously:

| Subagent | File | Responsibility |
|----------|------|---------------|
| geo-ai-visibility | `agents/geo-ai-visibility.md` | GEO audit, citability, AI crawlers, llms.txt, brand mentions |
| geo-platform-analysis | `agents/geo-platform-analysis.md` | Platform-specific optimization (ChatGPT, Perplexity, Google AIO) |
| geo-technical | `agents/geo-technical.md` | Technical SEO, Core Web Vitals, crawlability, indexability |
| geo-content | `agents/geo-content.md` | Content quality, E-E-A-T, readability, AI content detection |
| geo-schema | `agents/geo-schema.md` | Schema markup detection, validation, generation |

> **⚠️ CRITICAL**: Wait for ALL 5 subagents to return before proceeding to Phase 3. Do NOT generate reports or show results until all subagents complete. Premature reporting causes duplicate report generation with incorrect scores.

**Phase 3: Synthesis (Sequential — only after ALL subagents return)**
1. Collect all subagent reports — verify all 5 have returned
2. Calculate composite GEO Score (0-100)
3. **If `has-solution=true`**: Generate prioritized action plan
4. **Run GEU Quality Evaluation** (if API key available):
   - `python3 scripts/geu_evaluator.py <url> --provider claude --skip-rewrite`
   - Load output JSON into `audit-data.json["geu_score"]`
5. **Run GEO Impression Score** (if API key available):
   - `python3 scripts/geo_impression_score.py <url> --provider claude`
   - Load output JSON into `audit-data.json["geo_impression_score"]`
6. Assemble all audit data into a JSON file (`audit-data.json`)
7. Extract domain from URL (e.g., `ont.io` from `https://ont.io`)
8. Generate MD report: `python3 generate_md_report.py audit-data.json --dir ../<domain>` (run from scripts/ directory)
9. Generate PDF report: `python3 generate_pdf_report.py audit-data.json GEO-REPORT.pdf --dir ../<domain>`
10. Output both report files to the user (e.g., `ont.io/GEO-REPORT-<timestamp>.pdf`)

### Scoring Methodology

| Category | Weight | Measured By |
|----------|--------|-------------|
| AI Citability & Visibility | 25% | Passage scoring, answer block quality, AI crawler access |
| Brand Authority Signals | 20% | Mentions on Reddit, YouTube, Wikipedia, LinkedIn; entity presence |
| Content Quality & E-E-A-T | 20% | Expertise signals, original data, author credentials |
| Technical Foundations | 15% | SSR, Core Web Vitals, crawlability, mobile, security |
| Structured Data | 10% | Schema completeness, JSON-LD validation, rich result eligibility |
| Platform Optimization | 10% | Platform-specific readiness (Google AIO, ChatGPT, Perplexity) |

**When GEU Score is measured (7-category formula):**

| Category | Weight | Measured By |
|----------|--------|-------------|
| AI Citability & Visibility | 22% | Passage scoring, answer block quality, AI crawler access |
| Brand Authority Signals | 18% | Mentions on Reddit, YouTube, Wikipedia, LinkedIn; entity presence |
| Content Quality & E-E-A-T | 12% | Expertise signals, original data, author credentials |
| **GEU Quality Score** | **18%** | LLM-based content quality (Clarity, Depth, Balance, Breadth, Support, Insightfulness) |
| Technical Foundations | 13% | SSR, Core Web Vitals, crawlability, mobile, security |
| Structured Data | 8% | Schema completeness, JSON-LD validation, rich result eligibility |
| Platform Optimization | 9% | Platform-specific readiness (Google AIO, ChatGPT, Perplexity) |

**When both GEU and GEO Impression Score are measured (8-category formula):**

| Category | Weight | Measured By |
|----------|--------|-------------|
| AI Citability & Visibility | 20% | Passage scoring, answer block quality, AI crawler access |
| Brand Authority Signals | 15% | Mentions on Reddit, YouTube, Wikipedia, LinkedIn; entity presence |
| Content Quality & E-E-A-T | 10% | Expertise signals, original data, author credentials |
| **GEU Quality Score** | **15%** | LLM-based content quality (Clarity, Depth, Balance, Breadth, Support, Insightfulness) |
| Technical Foundations | 13% | SSR, Core Web Vitals, crawlability, mobile, security |
| Structured Data | 10% | Schema completeness, JSON-LD validation, rich result eligibility |
| Platform Optimization | 10% | Platform-specific readiness (Google AIO, ChatGPT, Perplexity) |
| GEO Impression Score | 7% | LLM citation frequency, position, content length (when measured) |

---

## Business Type Detection

Analyze homepage for patterns:

| Type | Signals |
|------|---------|
| **SaaS** | Pricing page, "Sign up", "Free trial", "/app", "/dashboard", API docs |
| **Local Service** | Phone number, address, "Near me", Google Maps embed, service area |
| **E-commerce** | Product pages, cart, "Add to cart", price elements, product schema |
| **Publisher** | Blog, articles, bylines, publication dates, article schema |
| **Agency** | Portfolio, case studies, "Our services", client logos, testimonials |
| **Other** | Default — apply general GEO best practices |

Adjust recommendations based on detected type. Local businesses need LocalBusiness schema and Google Business Profile optimization. SaaS needs SoftwareApplication schema and comparison page strategy. E-commerce needs Product schema and review aggregation.

---

## Sub-Skills (13 Specialized Components)

| # | Skill | Directory | Purpose |
|---|-------|-----------|---------|
| 1 | geo-audit | `skills/geo-audit/` | Full audit orchestration and scoring |
| 2 | geo-citability | `skills/geo-citability/` | Passage-level AI citation readiness |
| 3 | geo-crawlers | `skills/geo-crawlers/` | AI crawler access and robots.txt |
| 4 | geo-llmstxt | `skills/geo-llmstxt/` | llms.txt standard analysis and generation |
| 5 | geo-brand-mentions | `skills/geo-brand-mentions/` | Brand presence on AI-cited platforms |
| 6 | geo-platform-optimizer | `skills/geo-platform-optimizer/` | Platform-specific AI search optimization |
| 7 | geo-schema | `skills/geo-schema/` | Structured data for AI discoverability |
| 8 | geo-technical | `skills/geo-technical/` | Technical SEO foundations |
| 9 | geo-content | `skills/geo-content/` | Content quality and E-E-A-T |
| 10 | geo-report | `skills/geo-report/` | Client-ready deliverable generation |
| 11 | geo-prospect | `skills/geo-prospect/` | CRM-lite prospect and client pipeline management |
| 12 | geo-proposal | `skills/geo-proposal/` | Auto-generate client proposals from audit data |
| 13 | geo-compare | `skills/geo-compare/` | Monthly delta tracking and progress reports |

---

## Subagents (5 Parallel Workers)

| Agent | File | Skills Used |
|-------|------|-------------|
| geo-ai-visibility | `agents/geo-ai-visibility.md` | geo-citability, geo-crawlers, geo-llmstxt, geo-brand-mentions |
| geo-platform-analysis | `agents/geo-platform-analysis.md` | geo-platform-optimizer |
| geo-technical | `agents/geo-technical.md` | geo-technical |
| geo-content | `agents/geo-content.md` | geo-content |
| geo-schema | `agents/geo-schema.md` | geo-schema |

---

## Output Files

All commands generate structured output:

| Command | Output File |
|---------|------------|
| `/geo audit` | `GEO-AUDIT-REPORT.md` |
| `/geo page` | `GEO-PAGE-ANALYSIS.md` |
| `/geo citability` | `GEO-CITABILITY-SCORE.md` |
| `/geo crawlers` | `GEO-CRAWLER-ACCESS.md` |
| `/geo llmstxt` | `llms.txt` (ready to deploy) |
| `/geo brands` | `GEO-BRAND-MENTIONS.md` |
| `/geo platforms` | `GEO-PLATFORM-OPTIMIZATION.md` |
| `/geo schema` | `GEO-SCHEMA-REPORT.md` + generated JSON-LD |
| `/geo technical` | `GEO-TECHNICAL-AUDIT.md` |
| `/geo content` | `GEO-CONTENT-ANALYSIS.md` |
| `/geo report` | `GEO-CLIENT-REPORT.md` (presentation-ready) |
| `/geo report-pdf` | `GEO-REPORT.pdf` (professional PDF with charts) |
| `/geo quick` | Inline summary (no file) |
| `/geo prospect` | Updates `~/.geo-prospects/prospects.json` |
| `/geo proposal` | `~/.geo-prospects/proposals/<domain>-proposal-<date>.md` |
| `/geo compare` | `~/.geo-prospects/reports/<domain>-monthly-<YYYY-MM>.md` |
| `/geo rewrite` | `rewrite-prompt.md` (rewrite prompt for LLM) |
| `/geo evaluate` | `geu-evaluation.json` (quality scores + citation metrics) |
| `/geo impression` | `geo-impression.json` (citation visibility metrics) |

---

## PDF Report Generation

The `/geo report-pdf <url>` command generates a professional, branded PDF report:

### How It Works
1. Run the full audit or individual analyses first
2. Collect all scores and findings into a JSON structure
3. Execute the PDF generator: `python3 generate_pdf_report.py data.json GEO-REPORT.pdf --dir ../<domain>` (run from scripts/ directory)

### What the PDF Includes
- **Cover page** with GEO score gauge visualization
- **Score breakdown** with color-coded bar charts
- **AI Platform Readiness** dashboard with horizontal bar chart
- **Crawler Access** status table with color-coded Allow/Block
- **Key Findings** categorized by severity (Critical/High/Medium/Low)
- **Prioritized Action Plan** (Quick Wins, Medium-Term, Strategic)
- **Methodology & Glossary** appendix

### Workflow
1. First run `/geo audit <url>` to collect all data
2. Then run `/geo report-pdf <url>` to generate the PDF
3. The tool will compile audit data into JSON, then generate the PDF
4. Output: `<domain>/GEO-REPORT.pdf` (e.g., `ont.io/GEO-REPORT.pdf`)

---

## Quality Gates

- **Crawl limit:** Max 50 pages per audit (focus on quality over quantity)
- **Timeout:** 30 seconds per page fetch
- **Rate limiting:** 1-second delay between requests, max 5 concurrent
- **Robots.txt:** Always respect, always check
- **Duplicate detection:** Skip pages with >80% content similarity

---

## Quick Start Examples

```
# Full GEO audit (no solutions, include Chinese media - defaults)
/geo audit https://example.com

# Full GEO audit with action plan
/geo audit https://example.com has-solution=true

# Full GEO audit without Chinese media
/geo audit https://example.com cn-media=false

# Full GEO audit with solutions and Chinese media (explicit)
/geo audit https://example.com has-solution=true cn-media=true

# Full GEO audit with proxy (for geo-blocked sites)
/geo audit https://example.com has-solution=true use-proxy=true proxy_url=http://127.0.0.1:12377

# Check if AI bots can see your site
/geo crawlers https://example.com

# Score a specific page for AI citability
/geo citability https://example.com/blog/best-article

# Generate an llms.txt file for your site
/geo llmstxt https://example.com

# Get a 60-second visibility snapshot
/geo quick https://example.com

# Generate a client-ready report
/geo report https://example.com

# Rewrite content for AI visibility
/geo rewrite https://example.com

# Evaluate content quality with GEU scores (requires API key)
/geo evaluate https://example.com
/geo evaluate https://example.com --skip-rewrite
/geo evaluate https://example.com --provider claude --output geu.json

# Measure citation visibility with GEO Impression Score
/geo impression https://example.com
/geo impression https://example.com --query "What do they offer?"
/geo impression https://example.com --provider claude --output impression.json
```
