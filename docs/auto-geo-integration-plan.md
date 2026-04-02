# AutoGEO 集成计划

**日期:** 2026-04-02
**目标:** 将 AutoGEO 的核心功能集成到 geo-seo-claude 项目
**排除:** AutoGEO_Mini 微调训练功能

---

## 集成范围

| 优先级 | 功能 | 复杂度 | 预期效果 |
|--------|------|--------|----------|
| P0 | AutoGEO 规则库 → Action Plan 增强 | 低 | 报告质量提升 |
| P0 | `/geo rewrite` 命令 | 中 | 新增文档重写功能 |
| P1 | GEO Score 计算 | 中 | 可见性评估能力 |

---

## 1. AutoGEO 规则库集成

### 1.1 目标

将 AutoGEO 的内容优化规则作为 `quick_wins` 和 `medium_term` 建议的详细内容来源。

### 1.2 实施方案

创建 `scripts/autogeo_rules.py`:

```python
"""
AutoGEO Content Preference Rules
基于 AutoGEO 论文提取的内容优化规则库
"""

# 各引擎规则 (来自 core.py 的 _get_default_rules)

AUTOGEO_RULES = {
    "research_gemini": [...],  # Researchy-GEO + Gemini
    "research_gpt": [...],
    "research_claude": [...],
    "ecommerce_gemini": [...],  # E-commerce + Gemini
    "ecommerce_gpt": [...],
    "ecommerce_claude": [...],
    "geobench_gemini": [...],  # GEO-Bench + Gemini
    "geobench_gpt": [...],
    "geobench_claude": [...],
}

def get_rules_for_content_type(content_type: str, engine: str) -> list:
    """获取指定内容类型和引擎的规则"""
    key = f"{content_type}_{engine}"
    return AUTOGEO_RULES.get(key, AUTOGEO_RULES["research_gemini"])
```

### 1.3 规则映射到 Action Plan

| 规则类型 | → Action Plan 分类 |
|----------|-------------------|
| "Cite authoritative sources" | quick_wins: 添加引文和来源 |
| "Ensure factual accuracy" | medium_term: 验证内容准确性 |
| "Use specific details" | quick_wins: 添加具体数据和案例 |
| "Self-contained document" | quick_wins: 减少外部依赖 |
| "Clear structure" | quick_wins: 优化标题和段落结构 |

### 1.4 触发条件

- `has-solution=true` 时生效
- 根据网站业务类型匹配规则:
  - SaaS/Tech → Research rules
  - E-commerce → E-commerce rules
  - Publisher → Research rules

---

## 2. `/geo rewrite` 命令

### 2.1 目标

添加新命令 `geo rewrite <url>` 调用 AutoGEO 的 `rewrite_document()` 重写网页内容。

### 2.2 命令规格

```
/geo rewrite <url> [--engine gemini|gpt|claude] [--dataset research|ecommerce]
```

**参数:**
- `url`: 要重写的页面 URL
- `--engine`: 目标生成引擎 (默认: gemini)
- `--dataset`: 内容类型 (默认: research)

**输出:**
- 原始内容片段
- 重写后的内容
- 改进说明

### 2.3 实施方式

#### 方案 A: 调用 AutoGEO Python 包 (推荐)

```python
# scripts/geo_rewrite.py
import sys
sys.path.insert(0, "/Users/jasonzhou/work/python/AutoGEO")

from autogeo.rewriters import rewrite_document
from autogeo.config import Dataset

def rewrite_page(url: str, engine: str = "gemini", dataset: str = "research"):
    # 1. 获取页面内容
    content = fetch_page_content(url)

    # 2. 映射 dataset
    dataset_map = {
        "research": "Researchy-GEO",
        "ecommerce": "E-commerce",
    }
    ds = dataset_map.get(dataset, "Researchy-GEO")

    # 3. 调用 AutoGEO
    rewritten = rewrite_document(
        document=content,
        dataset=ds,
        engine_llm=engine
    )

    return rewritten
```

#### 方案 B: 直接使用规则重写 (无外部依赖)

```python
# 使用内置规则生成优化建议，不调用 AutoGEO 本身
def rewrite_with_rules(content: str, rules: list) -> str:
    """使用 AutoGEO 规则手动重写内容"""
    prompt = f"""原始内容:
{content}

请根据以下规则优化内容:
{chr(10).join(f"- {r}" for r in rules)}

重写后的内容:"""
    # 调用 LLM 重写
    return call_llm(prompt)
```

### 2.4 依赖

- AutoGEO 规则库 (直接复制到项目)
- LLM API 调用 (复用现有的 `call_gemini` 等)

---

## 3. GEO Score 计算

### 3.1 目标

在审计报告中添加基于 AutoGEO 方法的**可见性评分**。

### 3.2 AutoGEO GEO Score 方法

```python
# 来自 geo_score.py

def impression_wordpos_count_simple(sentences: list, n: int = 5) -> list:
    """基于位置和词数计算印象分"""
    # 位置衰减: exp(-i/total) 越靠前分数越高
    # 词数权重: 词数越多贡献越大
    # 引用分配: 同一句子多引用时均分

def impression_word_count_simple(sentences: list, n: int = 5) -> list:
    """基于词数计算印象分"""

def impression_pos_count_simple(sentences: list, n: int = 5) -> list:
    """仅基于位置计算印象分"""
```

### 3.3 集成方式

创建 `scripts/geo_impression_score.py`:

```python
"""
GEO Impression Score Calculator
基于 AutoGEO 方法计算内容在 AI 答案中的可见性
"""

def calculate_impression_score(
    content: str,
    query: str,
    engine: str = "gemini"
) -> dict:
    """
    计算内容对特定查询的可见性评分

    Returns:
        {
            "position_score": 0.0-1.0,    # 位置得分
            "word_count_score": 0.0-1.0, # 词数得分
            "combined_score": 0.0-1.0,   # 综合得分
            "recommendations": [...]      # 改进建议
        }
    """
    # 1. 调用 LLM 生成答案 (含引用)
    answer = generate_answer_with_citations(query, content, engine)

    # 2. 提取引用 [1], [2], ...
    citations = extract_citations(answer)

    # 3. 计算印象分
    scores = impression_wordpos_count_simple(citations)

    return scores
```

### 3.4 使用场景

- 在审计报告中添加 "预期可见性" 评估
- 重写前后对比可见性提升
- 作为内容质量的补充指标

---

## 实施顺序

```
Phase 1: 规则库集成
├── 创建 scripts/autogeo_rules.py
├── 更新 generate_md_report.py 使用规则
└── 测试输出

Phase 2: Rewrite 命令
├── 创建 scripts/geo_rewrite.py
├── 添加 /geo rewrite 到 SKILL.md
└── 测试重写功能

Phase 3: Impression Score
├── 创建 scripts/geo_impression_score.py
├── 集成到审计流程
└── 在报告中展示
```

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/autogeo_rules.py` | 新增 | AutoGEO 规则库 |
| `scripts/geo_rewrite.py` | 新增 | 重写功能 |
| `scripts/geo_impression_score.py` | 新增 | 可见性评分 |
| `scripts/generate_md_report.py` | 修改 | 使用规则增强 Action Plan |
| `SKILL.md` | 修改 | 添加 `/geo rewrite` 命令 |

---

## 风险与注意事项

1. **API 成本**: 重写功能需要 LLM API 调用
2. **中文适配**: AutoGEO 规则基于英文内容，需验证中文效果
3. **依赖**: 方案 A 需要访问 AutoGEO 代码库
4. **评估**: Impression Score 需要实际 LLM 答案来计算

---

## 验证方法

```bash
# 1. 规则库集成测试
python3 scripts/generate_md_report.py test/audit-data.json --dir test

# 2. Rewrite 功能测试
/geo rewrite https://example.com --engine gemini

# 3. Impression Score 测试
python3 scripts/geo_impression_score.py --url https://example.com --query "..."
```
