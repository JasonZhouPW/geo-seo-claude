# geo-seo-claude 功能指标扩展建议

> 分析时间：2026-04-08
> 基于：项目现状分析 + GEO 领域最新趋势

---

## 一、内容分析层（Content Analysis）

### 1. 多模态内容分析 ⭐⭐⭐⭐⭐（严重缺失）

| 新增指标 | 说明 | 对应平台 |
|----------|------|----------|
| **图像 alt text 覆盖率** | 有 alt text 的图片比例 | Gemini / Perplexity（多模态索引）|
| **视频内容索引友好度** | YouTube 描述优化度、字幕/文稿存在性 | Gemini |
| **图表/信息图可解析性** | 图注详细程度、数据来源标注 | 所有平台 |
| **音频内容文字稿** | 播客是否有对应文字版 | Gemini / ChatGPT |

> **为什么重要**：Gemini 和 Perplexity 正在向多模态全面转型，2026 年超过 40% 的 AI 引用将涉及图像/视频片段。

---

### 2. 内容新鲜度动态分析 ⭐⭐⭐⭐（中等缺失）

| 新增指标 | 说明 |
|----------|------|
| **Content Decay Rate（内容衰减率）** | 内容发布后多久开始在 AI 引用中消失 |
| **Recency Signal Score** | 发布时间、更新时间、结构化更新频率的综合评分 |
| **Perplexity Daily Index 匹配度** | 内容是否满足每日索引的更新节奏要求 |
| **Evergreen Content Index** | 内容是否为 evergreen（长期有效 vs 时效性）|

---

### 3. 内容原创度与深度分析 ⭐⭐⭐⭐（中等缺失）

| 新增指标 | 说明 |
|----------|------|
| **Original Research Score** | 是否包含原创数据/调研（AI 最偏好，引用提升 40%+） |
| **Claim Density** | 每千字的独立可引用观点数量 |
| **AI-Generated Content Detection** | 内容是否被识别为 AI 生成（影响引用权重） |
| **Internal Duplicate Score** | 站点内内容重复程度 |
| **Topical Comprehensiveness** | 主题覆盖的全面程度（vs 竞争对手）|

---

## 二、实体与关系层（Entity & Knowledge Graph）

### 4. 知识图谱实体分析 ⭐⭐⭐⭐⭐（严重缺失）

| 新增指标 | 说明 |
|----------|------|
| **Entity Recognition Score** | 品牌/人/产品等实体被知识图谱识别的完整度 |
| **Entity Relationship Density** | 实体间关系（vs X / 用于 Y / 创始人 Z）的丰富程度 |
| **Knowledge Triple Coverage** | 主谓宾三元组（Entity-Attribute-Value）的覆盖率 |
| **Entity Co-occurrence Analysis** | 品牌与行业术语的共现频率 |
| **Competitor Entity Comparison** | vs 竞品在知识图谱中的实体权重对比 |

---

### 5. E-E-A-T 信号深化 ⭐⭐⭐⭐（有基础，可深化）

| 新增指标 | 深化方向 |
|----------|----------|
| **Author Credentials** | 增加学术背景/行业认证的权威性评分 |
| **Experience Signals** | 细化"经验"维度：行业年限、项目案例、UGC |
| **Citation Network Quality** | 分析引用来源的 E-E-A-T 而非仅仅数量 |
| **Conflict of Interest Disclosure** | 是否有利益冲突声明（AI 对透明度的偏好上升）|

---

## 三、平台差异化层（Platform-Specific）

### 6. 各平台专项就绪度深化 ⭐⭐⭐⭐⭐（有但可深化）

| 平台 | 当前检测 | 可新增指标 |
|------|----------|------------|
| **Perplexity** | 基础 | 每日索引匹配度、内容新鲜度权重 |
| **ChatGPT** | 基础 | 品牌权威性综合分、Shopping Ready 度（电商） |
| **Google AI Overviews** | 基础 | Featured Snippet 适合度、SGE 引用模式 |
| **Gemini** | 基础 | 多模态信号完整度（图片+视频+音频）|
| **Claude** | 完全缺失 | Anthropic 最佳引用模式匹配度 |
| **Bing Copilot** | 基础 | Microsoft 365 生态集成度 |
| **百度文心/通义** | 完全缺失 | 中国 AI 平台适配（如果面向中国市场）|

---

### 7. AI Shopping 适配度 ⭐⭐⭐⭐（完全缺失，电商关键）

| 新增指标 | 说明 |
|----------|------|
| **Product Data Completeness** | 价格/库存/规格等字段完整性 |
| **Price Freshness** | 价格是否实时更新 |
| **Review Aggregation Score** | 用户评价数量和质量 |
| **Shopping Intent Match** | 内容是否匹配 shopping intent 查询 |
| **Direct Purchase Readiness** | 是否支持 AI 直接购买的格式要求 |

---

## 四、竞争情报层（Competitive Intelligence）

### 8. 竞品对比分析 ⭐⭐⭐⭐（严重缺失）

| 新增指标 | 说明 |
|----------|------|
| **AI Share of Voice vs 竞品** | 品牌在同类查询中被引用的比例 vs 竞品 |
| **Competitive Gap Analysis** | 与竞品在各维度上的差距雷达图 |
| **Competitive Citation History** | 竞品被引用频率的时间变化趋势 |
| **Keyword AI Visibility Landscape** | 核心关键词在 AI 搜索中的品牌分布 |
| **Market Presence Score** | 在 AI 搜索结果中的整体市场份额估算 |

---

### 9. 行业基准对比 ⭐⭐⭐（缺失）

| 新增指标 | 说明 |
|----------|------|
| **Industry GEO Score Benchmark** | 与同行业平均分对比（需积累行业数据） |
| **Category Leader Analysis** | 行业标杆的 GEO 策略拆解 |
| **Best Practice Extraction** | 从高表现竞品中提取可复用的 GEO 策略 |

---

## 五、信任与合规层（Trust & Compliance）

### 10. Trust Score 体系 ⭐⭐⭐⭐（缺失）

| 新增指标 | 说明 |
|----------|------|
| **Factual Accuracy Score** | 内容中事实陈述的可验证准确率 |
| **Source Authority Score** | 引用的外部来源权威性 |
| **Conflict of Interest Signal** | 商业利益声明的透明度 |
| **Security Signals** | HTTPS / 隐私政策 / 条款完整性 |
| **Accessibility Score** | WCAG 合规程度（AI 对无障碍内容有偏好）|

---

### 11. AI 代理（Agentic AI）就绪度 ⭐⭐⭐⭐（未来趋势，完全缺失）

| 新增指标 | 说明 |
|----------|------|
| **API-Ready Content Score** | 内容是否支持机器调用（而非仅人类阅读） |
| **Structured Data for Agents** | 是否支持 Agent 解析的结构化格式 |
| **Action Trigger Readiness** | 内容是否支持 AI 代理直接触发行动（预订/购买/填表）|
| **Tool-Use Compatibility** | 是否适配 AI Agent 的工具调用模式 |

---

## 六、测量与归因层（Measurement & Attribution）

### 12. GEO 转化归因 ⭐⭐⭐⭐（缺失，连接审计和商业价值）

| 新增指标 | 说明 |
|----------|------|
| **GEO-Attributed Traffic** | 因 AI 引用而带来的流量估算 |
| **GEO-Influenced Conversion** | 受 AI 引用影响但非直接归因的转化 |
| **Citation-to-Lead Time** | 从 AI 引用到产生销售线索的平均时间 |
| **Zero-Click Value Estimation** | 不依赖点击的 AI 曝光商业价值估算 |
| **GEO ROI Projection** | 基于当前分数和行业转化率的 ROI 预测 |

---

### 13. 跨平台可比性标准化 ⭐⭐⭐（缺失）

| 新增指标 | 说明 |
|----------|------|
| **Normalized GEO Score** | 跨平台标准化后的统一分数 |
| **Platform-Specific Weight** | 根据目标市场自动调整各平台权重 |
| **Cross-Platform Citation Consistency** | 同一内容在不同平台的引用一致性 |
| **Multi-Platform Visibility Index** | 综合所有平台的出现频率和位置加权分 |

---

## 七、内容运营层（Content Operations）

### 14. 内容节奏与 Pipeline 分析 ⭐⭐⭐（缺失，面向持续运营）

| 新增指标 | 说明 |
|----------|------|
| **Content Freshness Calendar** | 内容更新时间分布的健康度 |
| **Content Gap Identification** | 哪些高价值查询词尚无内容覆盖 |
| **Intent Coverage Map** | 信息型/商业型/交易型查询的内容覆盖完整度 |
| **Content-to-Entity Alignment** | 内容主题与品牌实体战略的对齐度 |
| **Seasonal Content Readiness** | 是否有针对季节性/事件性查询的预埋内容 |

---

## 优先级建议

| 优先级 | 新增指标 | 理由 |
|--------|----------|------|
| 🔴 极高 | 多模态分析 / 竞品对比 / 实体图谱 | 市场差异化核心 |
| 🔴 高 | AI Shopping 适配 / Agentic 就绪度 / GEO 归因 | 2026-2027 趋势 |
| 🟡 中 | Trust Score / 内容原创度 / 平台深化 | 深度护城河 |
| 🟢 低 | 行业基准 / 内容节奏分析 | 需要数据积累 |

---

*本建议基于 2026-04-08 的项目现状分析和 GEO 领域最新趋势，供功能扩展路线图参考。*
