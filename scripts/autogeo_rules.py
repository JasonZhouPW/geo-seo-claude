"""
AutoGEO Content Preference Rules
基于 AutoGEO 论文 (ICLR 2026) 提取的内容优化规则库

原文: https://arxiv.org/abs/2510.11438
"""

# AutoGEO 默认规则 - 按数据集和引擎分类

AUTOGEO_RULES = {
    # Researchy-GEO + Gemini
    "research_gemini": [
        "Attribute all factual claims to credible, authoritative sources with clear citations.",
        "Cover the topic comprehensively, addressing all key aspects and sub-topics.",
        "Ensure information is factually accurate and verifiable.",
        "Focus exclusively on the topic, eliminating irrelevant information, navigational links, and advertisements.",
        "Maintain a neutral, objective tone, avoiding promotional language, personal opinions, and bias.",
        "Maintain high-quality writing, free from grammatical errors, typos, and formatting issues.",
        "Present a balanced perspective on complex topics, acknowledging multiple significant viewpoints or counter-arguments.",
        "Present information as a self-contained unit, not requiring external links for core understanding.",
        "Provide clear, specific, and actionable steps.",
        "Provide explanatory depth by clarifying underlying causes, mechanisms, and context ('how' and 'why').",
        "State the key conclusion at the beginning of the document.",
        "Structure content logically with clear headings, lists, and paragraphs to ensure a cohesive flow.",
        "Substantiate claims with specific, concrete details like data, statistics, or named examples.",
        "Use clear and concise language, avoiding jargon, ambiguity, and verbosity.",
        "Use current information, reflecting the latest state of knowledge.",
    ],

    # Researchy-GEO + GPT
    "research_gpt": [
        "Attribute all claims to specific, credible, and authoritative sources.",
        "Create a self-contained document, free from non-informational content like advertisements, navigation, or paywalls.",
        "Ensure all content is strictly relevant to the core topic, excluding tangential or unrelated information.",
        "Ensure all information is factually accurate, verifiable, and internally consistent.",
        "Ensure content is fully accessible without requiring logins, subscriptions, or payments.",
        "Ensure information is current and up-to-date, especially for time-sensitive topics.",
        "Explain underlying mechanisms and causal relationships (the 'how' and 'why'), not just descriptive facts.",
        "Maintain a neutral and objective tone, prioritizing factual information over subjective opinions or biased language.",
        "Maintain a purely informational purpose, avoiding promotional, persuasive, or interactive content.",
        "Organize content with a clear, logical structure, using elements like headings and lists to improve readability.",
        "Present a balanced perspective on complex topics by including multiple relevant viewpoints or counterarguments.",
        "Present information with a cohesive, logical flow, avoiding fragmented or contradictory statements.",
        "Provide comprehensive coverage of the topic, addressing its key facets, nuances, and relevant context.",
        "Provide specific, actionable guidance when the topic involves a task or problem-solving.",
        "State the key conclusion directly at the beginning of the document.",
        "Substantiate claims with specific evidence, such as quantifiable data or concrete examples.",
        "Use clear, concise, and unambiguous language, defining essential jargon and eliminating filler content.",
    ],

    # Researchy-GEO + Claude
    "research_claude": [
        "Cover the topic comprehensively by addressing all its key facets and relevant sub-topics.",
        "Dedicate each paragraph or self-contained section to a single, distinct idea.",
        "Ensure a cohesive narrative flow where ideas connect logically rather than appearing as disconnected facts.",
        "Ensure all information is factually accurate, internally consistent, and up-to-date.",
        "Ensure the document is self-contained, providing all necessary context without requiring readers to follow external links.",
        "Ensure the full text is programmatically accessible, without requiring logins, paywalls, or user interaction.",
        "Focus exclusively on a single topic, removing all tangential information, advertisements, and navigational elements.",
        "Illustrate concepts and support arguments with specific details, concrete examples, or data.",
        "Maintain a neutral, objective tone, clearly distinguishing facts from opinions and avoiding biased or promotional language.",
        "Organize content with a clear, logical hierarchy using headings, lists, or tables to facilitate machine parsing.",
        "Present a balanced perspective on debatable topics by acknowledging multiple significant viewpoints or counterarguments.",
        "Provide clear, actionable steps or practical guidance for procedural topics.",
        "Provide explanatory depth by detailing the underlying mechanisms, causes, and effects ('how' and 'why').",
        "State the primary conclusion directly at the beginning of the document.",
        "Substantiate all claims with citations to credible, authoritative sources.",
        "Use clear and unambiguous language, defining specialized or technical terms upon their first use.",
        "Write concisely, eliminating repetitive phrasing, filler content, and unnecessary verbosity.",
    ],

    # E-commerce + Gemini
    "ecommerce_gemini": [
        "Ensure all information is factually accurate, verifiable, and current for the topic.",
        "Establish credibility by citing authoritative sources, providing evidence, or demonstrating clear expertise.",
        "Justify recommendations and claims with clear reasoning, context, or comparative analysis like pros and cons.",
        "Organize content with a clear, logical structure using elements like headings, lists, and tables to facilitate scanning and parsing.",
        "Present information objectively, avoiding promotional bias and including balanced perspectives where applicable.",
        "Provide actionable information, such as step-by-step instructions or clear recommendations.",
        "Provide specific, verifiable details such as names, model numbers, technical specifications, and quantifiable data.",
        "Structure content into modular, self-contained units, such as distinct paragraphs or list items for each concept.",
        "Use clear, simple, and unambiguous language, defining any necessary technical terms or jargon.",
        "Write concisely, eliminating verbose language, filler content, and unnecessary repetition.",
    ],

    # E-commerce + GPT
    "ecommerce_gpt": [
        "Be complete and thorough, covering all key aspects and a sufficient range of options.",
        "Clearly define the document's scope, especially for broad or ambiguous topics.",
        "Ensure all factual information is accurate, verifiable, and objective.",
        "Ensure information is up-to-date, clearly indicating its publication or last-updated date.",
        "Ensure the document is a complete, self-contained unit, not truncated or missing essential information.",
        "Establish credibility by citing authoritative sources or explaining the methodology for arriving at conclusions.",
        "Maintain a neutral tone, free from bias, promotional language, and unsubstantiated claims.",
        "Organize content logically with a clear, hierarchical structure using elements like headings, lists, and tables for easy parsing.",
        "Present information concisely, eliminating verbose language, filler words, and unnecessary introductions.",
        "Prioritize the most critical information by placing it at the beginning of the document or relevant section.",
        "Provide actionable content, such as step-by-step instructions or clear recommendations.",
        "Provide context and explain the reasoning behind recommendations, conclusions, or complex information.",
        "Structure data in a way that allows for direct evaluation, such as in a table or a pros-and-cons list.",
        "Use simple, direct, and unambiguous language, defining any necessary technical jargon.",
        "Use specific, quantifiable details like names, metrics, and technical specifications instead of vague generalizations.",
    ],

    # E-commerce + Claude
    "ecommerce_claude": [
        "Eliminate all tangential or promotional information.",
        "Ensure all information is factually accurate and verifiable, supporting claims with citations to authoritative sources.",
        "Ensure core content is directly accessible, without requiring logins, paywalls, or complex navigation.",
        "Keep information current for time-sensitive topics and clearly state its timeliness.",
        "Maintain an objective, neutral tone and present a balanced perspective, including relevant pros and cons or alternative viewpoints where applicable.",
        "Maintain internal consistency in terminology, formatting, and data presentation, especially for comparable items.",
        "Organize content using a clear, logical, and consistent structure with elements like headings, lists, and tables to facilitate automated parsing.",
        "Provide actionable content, such as step-by-step instructions or direct recommendations.",
        "Provide context or rationale to explain the reasoning behind data, recommendations, or claims.",
        "Structure content into discrete, self-contained units, with each paragraph or section addressing a single concept.",
        "The document should provide the complete core information, without requiring navigation to external links for essential information.",
        "Use specific, quantifiable details like names, model numbers, and metrics instead of vague generalizations.",
        "Write with clarity and conciseness, using simple, direct language and eliminating unnecessary jargon, repetition, and filler.",
    ],

    # GEO-Bench + Gemini
    "geobench_gemini": [
        "Ensure all information is factually accurate and verifiable, citing credible sources.",
        "Ensure information is current and up-to-date, especially for time-sensitive topics.",
        "Ensure the document is self-contained and comprehensive, providing all necessary context and sub-topic information.",
        "Explain the underlying mechanisms and principles (the 'why' and 'how'), not just surface-level facts.",
        "Maintain a singular focus on the core topic, excluding tangential information, promotional content, and document 'noise' (e.g., navigation, ads).",
        "Organize content with a clear, logical hierarchy, using elements like headings, lists, and tables.",
        "Present a balanced and objective view on debatable topics, including multiple significant perspectives.",
        "Provide specific, actionable guidance, such as step-by-step instructions, for procedural topics.",
        "State the primary conclusion directly at the beginning of the document.",
        "Use clear and unambiguous language, defining technical terms, acronyms, and jargon upon first use.",
        "Use specific, concrete details and examples instead of abstract generalizations.",
        "Write concisely, eliminating verbose language, redundancy, and filler content.",
    ],

    # GEO-Bench + GPT
    "geobench_gpt": [
        "Address the topic comprehensively, covering all essential sub-topics and necessary context.",
        "Define essential terms, acronyms, and jargon upon their first use.",
        "Ensure all factual information is accurate, verifiable, and internally consistent.",
        "Ensure content is free from illegal, unethical, or harmful information.",
        "Ensure each document is self-contained, providing all necessary information on the topic without requiring external links.",
        "Explain the 'why' and 'how' behind facts, clarifying underlying principles and mechanisms.",
        "Explicitly differentiate between similar or easily confused concepts.",
        "For complex or debatable subjects, present multiple significant viewpoints in a balanced way.",
        "For procedural content, provide clear, numbered, step-by-step instructions.",
        "For time-sensitive topics, ensure information is current and clearly display its publication or last-updated date.",
        "Maintain a neutral, objective tone, clearly distinguishing facts from opinions.",
        "Maintain a singular focus on the core topic, excluding tangential or promotional content.",
        "Organize content with a clear, logical hierarchy using headings, lists, and tables.",
        "State the primary conclusion at the beginning of the document.",
        "Structure content into atomic units, where each paragraph or section addresses a single idea.",
        "Use clear, simple, and unambiguous language.",
        "Use concrete examples, analogies, or case studies to illustrate complex concepts.",
        "Use specific, concrete details like names, dates, and statistics instead of generalizations.",
        "Write concisely, eliminating repetition, filler words, and verbose phrasing.",
    ],

    # GEO-Bench + Claude
    "geobench_claude": [
        "Cite authoritative sources to support claims and establish credibility.",
        "Cover the topic comprehensively, providing depth by explaining the underlying 'why' and 'how'.",
        "Ensure all information is factually accurate, verifiable, and internally consistent.",
        "Ensure each document is self-contained and can be understood without external context.",
        "Focus on a single topic, writing concisely and eliminating irrelevant or repetitive content.",
        "For task-oriented topics, provide actionable guidance like step-by-step instructions.",
        "Indicate the timeliness of information with clear publication or revision dates.",
        "Maintain a neutral, objective tone, prioritizing facts over opinions or promotional language.",
        "Present multiple perspectives and counterarguments for complex or debatable topics.",
        "Provide specific details, such as names, dates, statistics, and concrete examples, to support claims and illustrate concepts.",
        "Segment content into discrete units, where each paragraph or list item addresses a single idea.",
        "State the key conclusion at the beginning of the document.",
        "Use clear structural elements like headings, lists, and tables to organize content logically.",
        "Use clear, unambiguous language, and define technical terms or acronyms on their first use.",
    ],
}

# 规则到 Action Plan 的映射
RULE_TO_CATEGORY = {
    "citation": "quick_wins",
    "source": "quick_wins",
    "cite": "quick_wins",
    "factual": "medium_term",
    "accurate": "medium_term",
    "verifiable": "medium_term",
    "specific": "quick_wins",
    "detail": "quick_wins",
    "example": "quick_wins",
    "self-contained": "quick_wins",
    "external link": "quick_wins",
    "structure": "quick_wins",
    "heading": "quick_wins",
    "list": "quick_wins",
    "table": "quick_wins",
    "conclusion": "quick_wins",
    "beginning": "quick_wins",
    "balance": "medium_term",
    "perspective": "medium_term",
    "actionable": "medium_term",
    "step": "medium_term",
    "instruction": "medium_term",
    "comprehensive": "medium_term",
    "depth": "medium_term",
    "mechanism": "medium_term",
    "why": "medium_term",
    "how": "medium_term",
    "current": "medium_term",
    "up-to-date": "medium_term",
    "definition": "quick_wins",
    "define": "quick_wins",
    "jargon": "quick_wins",
    "terminology": "quick_wins",
    "concise": "medium_term",
    "eliminate": "medium_term",
    "filler": "medium_term",
    "noise": "quick_wins",
    "navigation": "quick_wins",
    "advertisement": "quick_wins",
    "promotional": "medium_term",
    "bias": "medium_term",
    "neutral": "medium_term",
    "objective": "medium_term",
    "tone": "medium_term",
    "authoritative": "medium_term",
    "expertise": "medium_term",
    "trust": "medium_term",
    "accessible": "medium_term",
    "login": "medium_term",
    "paywall": "medium_term",
}

# 业务类型到规则集的映射
BUSINESS_TYPE_TO_RULES = {
    "saas": "research_gemini",
    "technology": "research_gemini",
    "ai": "research_gemini",
    "software": "research_gemini",
    "agency": "research_gemini",
    "publisher": "research_gemini",
    "blog": "research_gemini",
    "news": "research_gemini",
    "ecommerce": "ecommerce_gemini",
    "e-commerce": "ecommerce_gemini",
    "shop": "ecommerce_gemini",
    "store": "ecommerce_gemini",
    "local": "research_gemini",
    "other": "research_gemini",
}


def get_rules_key(business_type: str, engine: str = "gemini") -> str:
    """
    根据业务类型和目标引擎获取规则集键名

    Args:
        business_type: 业务类型 (saas, ecommerce, local, etc.)
        engine: 目标 AI 引擎 (gemini, gpt, claude)

    Returns:
        规则集键名 (如 "research_gemini", "ecommerce_gpt")
    """
    bt_lower = business_type.lower()
    engine_lower = engine.lower()

    # 获取业务类型对应的规则基础类型
    rule_base = BUSINESS_TYPE_TO_RULES.get(bt_lower, "research")

    return f"{rule_base}_{engine_lower}"


def get_rules_for_audit(business_type: str, engine: str = "gemini") -> list:
    """
    获取适合审计的规则列表

    Args:
        business_type: 业务类型
        engine: 目标 AI 引擎

    Returns:
        规则列表
    """
    key = get_rules_key(business_type, engine)
    return AUTOGEO_RULES.get(key, AUTOGEO_RULES["research_gemini"])


def rules_to_action_plan(rules: list) -> dict:
    """
    将规则列表转换为 Action Plan 格式

    Args:
        rules: AutoGEO 规则列表

    Returns:
        {"quick_wins": [...], "medium_term": [...], "strategic": [...]}
    """
    quick_wins = []
    medium_term = []
    strategic = []

    for rule in rules:
        rule_lower = rule.lower()

        # 分类
        category = "medium_term"  # 默认
        for keyword, cat in RULE_TO_CATEGORY.items():
            if keyword in rule_lower:
                category = cat
                break

        action = {
            "category": "content_optimization",
            "rule": rule,
            "priority": category
        }

        if category == "quick_wins":
            quick_wins.append(action)
        elif category == "medium_term":
            medium_term.append(action)
        else:
            strategic.append(action)

    # 去重
    seen = set()
    unique_quick = []
    for item in quick_wins:
        key = item["rule"]
        if key not in seen:
            seen.add(key)
            unique_quick.append(item)

    seen = set()
    unique_medium = []
    for item in medium_term:
        key = item["rule"]
        if key not in seen:
            seen.add(key)
            unique_medium.append(item)

    # 限制数量
    return {
        "quick_wins": unique_quick[:8],
        "medium_term": unique_medium[:6],
        "strategic": strategic[:4]
    }


if __name__ == "__main__":
    # 测试
    rules = get_rules_for_audit("saas", "gemini")
    print(f"Loaded {len(rules)} rules for SaaS + Gemini")
    print("\nSample rules:")
    for r in rules[:3]:
        print(f"  - {r}")

    action_plan = rules_to_action_plan(rules)
    print(f"\nAction Plan:")
    print(f"  quick_wins: {len(action_plan['quick_wins'])}")
    print(f"  medium_term: {len(action_plan['medium_term'])}")
    print(f"  strategic: {len(action_plan['strategic'])}")
