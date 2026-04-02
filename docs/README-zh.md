# GEO-SEO 分析工具 — 用户指南

> **理念：** GEO 优先，SEO 辅助。AI 搜索正在取代传统搜索。
> 本工具优化的是流量去向，而非流量来源。

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [命令参考](#命令参考)
- [理解 GEO 评分](#理解-geo-评分)
- [报告类型](#报告类型)
- [示例](#示例)
- [评分方法论](#评分方法论)
- [业务类型检测](#业务类型检测)
- [故障排除](#故障排除)

---

## 安装

### 环境要求

- Claude Code CLI（输入 `/help` 安装）
- Python 3.8+（用于生成报告）
- Git（用于克隆仓库）
- 网络连接（用于抓取网页）

### 方式一：自动化安装（推荐）

最简单的方式是使用 `install.sh` 脚本：

```bash
# 下载并运行安装脚本
curl -sL https://raw.githubusercontent.com/zubair-trabzada/geo-seo-claude/main/install.sh | bash

# 或者如果已有本地仓库
./install.sh
```

安装程序将自动完成：
- 检查环境前提条件（Git、Python 3.8+、Claude Code）
- 创建所需目录
- 安装主技能到 `~/.claude/skills/geo/`
- 安装 13 个子技能到 `~/.claude/skills/`
- 安装 5 个子代理到 `~/.claude/agents/`
- 安装工具脚本
- 安装架构模板
- 安装 Python 依赖
- 可选安装 Playwright（用于截图）
- 验证安装结果

### 方式二：手动安装

1. **克隆或复制仓库**到本地。

2. **运行安装脚本**：

   ```bash
   ./install.sh
   ```

   这会自动处理所有文件部署和依赖安装。

3. **或手动复制文件**：

   ```bash
   # 创建目录
   mkdir -p ~/.claude/skills/geo
   mkdir -p ~/.claude/agents

   # 复制技能文件
   cp geo/* ~/.claude/skills/geo/
   cp -r skills/*/ ~/.claude/skills/
   cp agents/*.md ~/.claude/agents/
   cp scripts/* ~/.claude/skills/geo/scripts/
   ```

4. **安装 Python 依赖**：

   ```bash
   pip install reportlab Pillow requests beautifulsoup4
   ```

### 验证安装

安装完成后，验证是否正常工作：

```
/geo help
```

如果安装成功，将看到 GEO-SEO 工具的帮助菜单，包含所有可用命令。

---

## 快速开始

### 60 秒快照

```bash
/geo quick https://example.com
```

### 完整 GEO 审计（5–10 分钟）

```bash
/geo audit https://example.com
```

### 带行动方案的完整审计

```bash
/geo audit https://example.com has-solution=true
```

---

## 命令参考

### `/geo audit <url> [has-solution] [cn-media]`

**完整的 GEO + SEO 审计，使用并行子代理委托。**

对 AI 引用性、平台分析、技术基础设施、内容质量和架构标记进行全面优化审计。

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `url` | 字符串 | 必填 | 目标网站 URL |
| `has-solution` | 布尔值 | `false` | 包含优先级行动方案 |
| `cn-media` | 布尔值 | `true` | 包含中国媒体平台（微信、微博、知乎等）|

**执行流程：**

1. **阶段 1 — 发现**：获取首页、检测业务类型、抓取站点地图/内部链接（最多 50 页）
2. **阶段 2 — 并行分析**：同时启动 5 个子代理：
   - `geo-ai-visibility` — 引用性、爬虫、llms.txt、品牌提及
   - `geo-platform-analysis` — ChatGPT、Perplexity、Google AIO 就绪度
   - `geo-technical` — 核心 Web 指标、SSR、可抓取性、安全性
   - `geo-content` — E-E-A-T、可读性、作者信号
   - `geo-schema` — JSON-LD 检测和验证
3. **阶段 3 — 综合**：计算综合 GEO 评分、生成 JSON + MD + PDF 报告

**输出文件：**
- `audit-data.json` — 原始审计数据
- `GEO-REPORT-{timestamp}.md` — Markdown 报告
- `GEO-REPORT-{timestamp}.pdf` — 专业 PDF 报告

**示例：**

```bash
# 基本审计（无行动方案，包含中国媒体）
/geo audit https://bigmodel.cn

# 带行动方案的完整审计
/geo audit https://bigmodel.cn has-solution=true

# 不包含中国媒体的审计
/geo audit https://bigmodel.cn cn-media=false

# 完整审计（显式指定所有参数）
/geo audit https://bigmodel.cn has-solution=true cn-media=true
```

---

### `/geo page <url>`

**深度单页 GEO 分析。**

详细分析单个页面——内容结构、架构标记、元标签、标题层级和 AI 引用性。

```bash
/geo page https://bigmodel.cn/pricing
```

---

### `/geo citability <url>`

**评估内容对 AI 引用的适配度。**

评估内容对 AI 系统的可引用性和可提取性。考虑因素：
- 句子结构和清晰度
- 统计数字和事实的存在
- 答案块优化
- 段落级评分

```bash
/geo citability https://bigmodel.cn/blog
```

---

### `/geo crawlers <url>`

**检查 AI 爬虫访问权限（robots.txt 分析）。**

分析 AI 系统是否能访问您的网站：

| 爬虫 | 描述 |
|------|------|
| GPTBot | OpenAI（ChatGPT）|
| Claude（ClaudeBot）| Anthropic |
| Google-Extended | Google（AI Overviews）|
| CCBot | Common Crawl |
| PerplexityBot | Perplexity |

```bash
/geo crawlers https://bigmodel.cn
```

---

### `/geo llmstxt <url>`

**分析或生成 llms.txt 文件。**

`llms.txt` 是由 Andrew Ng 创建的新标准，帮助 AI 系统理解您的网站结构。此命令：

1. 检查 `llms.txt` 是否存在
2. 验证 content-type 头（必须是 `text/plain`）
3. 分析完整性和质量
4. 如果缺失则生成模板

```bash
/geo llmstxt https://bigmodel.cn
```

---

### `/geo brands <url>`

**扫描 AI 引用平台上的品牌提及。**

扫描 AI 模型频繁引用的平台上的品牌存在情况：

**国际平台：**
- Wikipedia
- LinkedIn
- YouTube
- GitHub
- Reddit

**中国平台**（当 `cn-media=true`）：
- 微信
- 微博
- 知乎
- B站
- 抖音

```bash
/geo brands https://bigmodel.cn
/geo brands https://bigmodel.cn cn-media=false
```

---

### `/geo platforms <url>`

**平台特定优化分析。**

评估主要 AI 平台的就绪度：

| 平台 | 描述 |
|------|------|
| Google AI Overviews | Google 的 AI 驱动搜索结果 |
| ChatGPT | OpenAI 的对话式 AI |
| Perplexity | AI 驱动的搜索引擎 |
| Google Gemini | Google 的多模态 AI |
| Bing Copilot | Microsoft 的 AI 助手 |

```bash
/geo platforms https://bigmodel.cn
```

---

### `/geo schema <url>`

**检测、验证和生成结构化数据。**

分析您网站上的 Schema.org 标记并提供：
- JSON-LD 检测和验证
- 缺失的架构类型建议
- 生成的架构模板

```bash
/geo schema https://bigmodel.cn
```

---

### `/geo technical <url>`

**传统技术 SEO 审计。**

涵盖：
- 服务器端渲染（SSR）检测
- 核心 Web 指标就绪度
- 可抓取性和可索引性
- HTTPS 和安全头
- 移动端优化
- hreflang 标签

```bash
/geo technical https://bigmodel.cn
```

---

### `/geo content <url>`

**内容质量和 E-E-A-T 评估。**

评估：
- **经验（Experience）** — 第一手知识信号
- **专业知识（Expertise）** — 学科专业知识
- **权威性（Authoritativeness）** — 行业权威
- **可信度（Trustworthiness）** — 信誉和可靠性
- 作者简介和资质
- 内容新鲜度和深度
- 来源引用

```bash
/geo content https://bigmodel.cn
```

---

### `/geo report <url>`

**生成客户就绪的 GEO 交付物。**

创建可直接展示的 Markdown 报告，包含：
- 执行摘要
- 评分明细
- 按严重程度分类的主要发现
- 优先级行动方案

```bash
/geo report https://bigmodel.cn
```

---

### `/geo report-pdf <url>`

**生成带图表和专业评分的企业 PDF 报告。**

创建包含以下内容的品牌 PDF：
- 带 GEO 评分仪表的封面
- 颜色编码的评分条形图
- AI 平台就绪度仪表板
- 爬虫访问状态表
- 按严重程度分类的主要发现
- 优先级行动方案
- 方法论附录

```bash
/geo report-pdf https://bigmodel.cn
```

---

### `/geo quick <url>`

**60 秒 GEO 可见度快照。**

快速 inline 分析，涵盖：
- 业务类型检测
- 前 3 大优势
- 前 3 大问题
- 快速见效的改进

```bash
/geo quick https://bigmodel.cn
```

---

### `/geo rewrite <url> [--engine gemini|gpt|claude] [--prompt-only]`

**使用 AutoGEO 规则重写页面内容以提高 AI 可见度。**

生成可输入 LLM 的重写提示，以优化内容的 AI 引用。

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `--engine` | `gemini` | 目标 AI 平台 |
| `--prompt-only` | — | 仅输出重写提示，不调用 LLM |

```bash
# 为 Gemini 生成重写提示
/geo rewrite https://bigmodel.cn

# 针对 GPT 优化
/geo rewrite https://bigmodel.cn --engine gpt

# 仅查看提示（不执行）
/geo rewrite https://bigmodel.cn --prompt-only
```

---

### `/geo prospect <cmd>`

**轻量级 CRM — 管理销售管道中的潜在客户。**

命令：

| 命令 | 描述 |
|------|------|
| `list` | 列出所有潜在客户 |
| `add <域名> <阶段>` | 添加新潜在客户 |
| `update <域名> <阶段>` | 更新潜在客户阶段 |
| `notes <域名> <备注>` | 添加备注 |

**阶段：** `lead` → `qualified` → `proposal` → `negotiation` → `won` → `lost`

```bash
/geo prospect list
/geo prospect add example.com lead
/geo prospect update example.com qualified
/geo prospect notes example.com "计划下周演示"
```

---

### `/geo proposal <域名>`

**从审计数据自动生成客户提案。**

基于最新审计为域名创建专业提案文档。

```bash
/geo proposal bigmodel.cn
```

输出：`~/.geo-prospects/proposals/{domain}-proposal-{date}.md`

---

### `/geo compare <域名>`

**月度对比报告 — 向客户展示评分改进。**

比较域名的前两次审计并显示：
- 各类别评分变化
- 发现的新问题
- 已解决的问题
- 进展摘要

```bash
/geo compare bigmodel.cn
```

输出：`~/.geo-prospects/reports/{domain}-monthly-{YYYY-MM}.md`

---

## 理解 GEO 评分

### 评分范围

| 范围 | 评级 | 解释 |
|------|------|------|
| 90–100 | 优秀 | 顶级 GEO 优化；极有可能被 AI 引用 |
| 75–89 | 良好 | 强大的 GEO 基础，有改进空间 |
| 60–74 | 一般 | 中等的 GEO 存在；存在重大优化机会 |
| 40–59 | 较差 | 较弱的 GEO 信号；AI 系统可能难以引用 |
| 0–39 | 极差 | 极少的 GEO 优化；对 AI 系统基本不可见 |

### 评分类别

| 类别 | 权重 | 衡量内容 |
|------|------|----------|
| AI 引用性 | 25% | 内容对 AI 系统的可引用性/可提取性 |
| 品牌权威 | 20% | 第三方提及、实体识别信号 |
| 内容 E-E-A-T | 20% | 经验、专业知识、权威性、可信度 |
| 技术 GEO | 15% | AI 爬虫访问、llms.txt、渲染、速度 |
| 架构和结构化数据 | 10% | Schema.org 标记质量和完整性 |
| 平台优化 | 10% | AI 模型训练和引用平台的存在度 |

**注意：** 当测量时，会包含**第7个类别 — GEO 印象分数**，权重为 14%。该分数评估网站在 LLM 生成答案中的出现情况，基于引用频率、位置和内容长度。未测量时显示 0% 并从公式中排除。

**公式（6类别，标准）：**
```
GEO_Score = (引用性 × 0.25) + (品牌 × 0.20) + (E-E-A-T × 0.20) + (技术 × 0.15) + (架构 × 0.10) + (平台 × 0.10)
```

**公式（7类别，含 GEO 印象分数）：**
```
GEO_Score = (引用性 × 0.22) + (品牌 × 0.18) + (E-E-A-T × 0.18) + (技术 × 0.12) + (架构 × 0.08) + (平台 × 0.08) + (印象分数 × 0.14)
```

### 问题严重程度分类

**严重（立即修复）：**
- robots.txt 中阻止了所有 AI 爬虫
- 无可索引内容（仅客户端渲染）
- 域名级别的 noindex 指令
- 关键页面返回 5xx 错误
- 完全缺少结构化数据

**高优先级（1 周内修复）：**
- 阻止了关键 AI 爬虫
- 不存在 llms.txt 文件
- 缺少 Organization 架构
- 内容页面没有作者署名

**中优先级（1 个月内修复）：**
- 部分 AI 爬虫被阻止
- llms.txt 存在但不完整
- 缺少 FAQ 架构
- 作者简介缺乏资质

**低优先级（尽可能优化）：**
- 微小的架构验证错误
- 部分图片缺少 alt 文本
- 缺少 Open Graph 标签

---

## 报告类型

### JSON 数据（`audit-data.json`）

用于程序处理的原始审计数据：
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

### Markdown 报告（`GEO-REPORT-{timestamp}.md`）

人类可读的通用报告，包含：
- 执行摘要
- 评分明细
- 按类别分类的详细发现
- 行动方案（当 `has-solution=true`）

### PDF 报告（`GEO-REPORT-{timestamp}.pdf`）

专业的客户交付报告，包含：
- 带 GEO 评分仪表的封面
- 颜色编码的评分图表
- AI 平台就绪度仪表板
- 爬虫访问状态表
- 按严重程度分类的发现
- 优先级行动方案
- 方法论附录

---

## 示例

### 示例 1：新客户的初始审计

```bash
# 1. 快速快照评估潜力
/geo quick https://acme.com

# 2. 带行动方案的完整审计
/geo audit https://acme.com has-solution=true cn-media=true

# 3. 生成 PDF 用于客户交付
/geo report-pdf https://acme.com
```

### 示例 2：技术深入分析

```bash
# 检查 AI 可能无法引用您内容的原因
/geo technical https://acme.com

# 验证爬虫访问权限
/geo crawlers https://acme.com

# 检查 llms.txt 状态
/geo llmstxt https://acme.com
```

### 示例 3：内容优化

```bash
# 评估内容质量
/geo content https://acme.com/blog

# 对特定页面进行引用性评分
/geo citability https://acme.com/blog/best-post

# 生成重写提示
/geo rewrite https://acme.com/blog/best-post --engine gpt
```

### 示例 4：平台特定策略

```bash
# 检查 ChatGPT/Perplexity 就绪度
/geo platforms https://acme.com

# 扫描品牌提及
/geo brands https://acme.com
```

### 示例 5：客户管理

```bash
# 添加新潜在客户
/geo prospect add acme.com lead

# 审计后，生成提案
/geo proposal acme.com

# 下个月，展示进展
/geo compare acme.com
```

---

## 评分方法论

### 业务类型检测

工具自动将网站分类为：

| 类型 | 检测信号 |
|------|----------|
| **SaaS** | 定价页面、"注册"、"免费试用"、/app 子域名、功能对比表 |
| **本地商家** | 地址、电话、Google Maps、"附近"、服务区域页面 |
| **电商** | 产品页面、购物车、"加入购物车"、价格展示、产品架构 |
| **出版商** | 博客、文章、署名、发布日期、文章架构 |
| **代理商** | 作品集、案例研究、"我们的服务"、客户徽标、推荐信 |

### 抓取限制

- 每完整审计最多 **50 页**
- 每页面抓取 **30 秒超时**
- 请求间隔 **1 秒延迟**
- 始终遵守 **robots.txt** 指令

---

## 故障排除

### "llms.txt 返回 HTML 而不是文本"

这意味着您的服务器返回的是 `Content-Type: text/html` 而不是 `Content-Type: text/plain`。通过配置 Web 服务器以正确的 content type 提供 `llms.txt` 来修复。

### "AI 引用性评分非常低"

常见原因：
1. **客户端渲染（SPA）** — AI 爬虫只能看到加载屏幕
2. **内容单薄** — 没有足够的实质性文本
3. **缺少统计数据或事实** — AI 偏好可引用的数据
4. **标题结构差** — 难以解析为答案块

### "品牌权威评分低"

AI 模型使用第三方信号进行实体识别：
- Wikipedia 存在（创建/编辑 Wikipedia 页面）
- 带订阅者的 YouTube 频道
- 有员工档案的 LinkedIn 公司页面
- 权威网站的新闻提及
- 行业奖项和认证

### "架构评分为 0"

您的网站可能没有 JSON-LD 结构化数据。使用：
```bash
/geo schema https://your-site.com
```
获取特定的架构建议和模板。

### PDF 生成失败

安装依赖：
```bash
pip install reportlab Pillow requests beautifulsoup4
```

### 报告未生成

检查所有 5 个子代理是否成功完成。如果阶段 2 失败，阶段 3 不会运行。重新运行审计：
```bash
/geo audit https://your-site.com has-solution=true
```

---

## 术语表

| 术语 | 定义 |
|------|------|
| **GEO** | 生成式引擎优化 — 优化内容以获得 AI 引用 |
| **AI 引用性** | 内容对 AI 系统的可提取性和可引用性 |
| **llms.txt** | 帮助 AI 系统理解您网站结构的文本文件 |
| **E-E-A-T** | 经验、专业知识、权威性、可信度 |
| **结构化数据** | Schema.org 标记帮助搜索引擎理解内容 |
| **AI Overviews** | Google 的 AI 驱动搜索结果（原 SGE）|
| **实体识别** | AI 系统识别和理解品牌/概念的方式 |
| **SSR** | 服务器端渲染 — JavaScript 执行前内容已可用 |
| **CSR** | 客户端渲染 — JavaScript 运行后才能获取内容 |

---

## 支持

如遇问题或功能请求，请在以下地址提交 issue：
https://github.com/your-repo/geo-seo-claude/issues
