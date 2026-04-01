#!/usr/bin/env python3
"""
Brand Mention Scanner — Checks brand presence across AI-cited platforms (Global + China).

Brand mentions correlate 3x more strongly with AI visibility than backlinks.
(Ahrefs December 2025 study of 75,000 brands)

Platform importance for AI citations:
1. YouTube mentions (~0.737 correlation - STRONGEST)
2. Reddit mentions (high)
3. Wikipedia presence (high)
4. LinkedIn presence (moderate)

China-specific platforms:
1. 抖音 (Douyin) - 最高权重，品牌短视频和直播核心平台
2. 小红书 (Xiaohongshu/RED) - 种草经济核心，KOC/KOL影响力巨大
3. 知乎 - 专业问答，品牌权威性
4. 微信 - 公众号+视频号联动
5. 哔哩哔哩 - 年轻用户，技术/测评内容
"""

import sys
import json
import re
import os
from typing import Optional
from urllib.parse import quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

# Optional Tavily search for enhanced platform detection
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TavilyClient = None  # type: ignore
    TAVILY_AVAILABLE = False


def get_tavily_client() -> Optional["TavilyClient"]:
    """Get Tavily client if API key is available."""
    if not TAVILY_AVAILABLE:
        return None
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return None
    try:
        return TavilyClient(api_key=api_key)
    except Exception:
        return None


def tavily_search(brand_name: str, platform_hints: list[str] = None) -> dict:
    """
    Use Tavily API to search for brand mentions across platforms.

    Args:
        brand_name: Brand name to search for
        platform_hints: Optional list of platform names to focus search

    Returns:
        dict with search results and analysis
    """
    client = get_tavily_client()
    if not client:
        return {
            "available": False,
            "error": "Tavily API key not found. Set TAVILY_API_KEY environment variable.",
            "setup_instructions": [
                "1. Get API key from https://tavily.com",
                "2. Run: export TAVILY_API_KEY=your_api_key",
                "3. Re-run this script",
            ],
        }

    try:
        # Build search query with platform hints
        query = brand_name
        if platform_hints:
            query = f"{brand_name} {' '.join(platform_hints)}"

        # Perform search
        results = client.search(
            query=query,
            search_depth="basic",
            max_results=10,
            include_answer=True,
            include_raw_content=False,
        )

        return {
            "available": True,
            "query": query,
            "answer": results.get("answer"),
            "results": [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content", "")[:200] + "..." if len(r.get("content", "")) > 200 else r.get("content", ""),
                }
                for r in results.get("results", [])
            ],
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def analyze_tavily_results_for_platforms(tavily_result: dict, brand_name: str) -> dict:
    """
    Analyze Tavily search results to detect platform presence.

    Args:
        tavily_result: Result from tavily_search()
        brand_name: Brand name being analyzed

    Returns:
        dict with platform presence analysis
    """
    if not tavily_result.get("available"):
        return {"analyzed": False, "error": tavily_result.get("error")}

    analysis = {
        "analyzed": True,
        "brand_name": brand_name,
        "platforms_detected": [],
        "platform_details": {},
    }

    # Platform detection patterns
    platform_patterns = {
        # Chinese platforms
        "抖音": [r"douyin\.com", r"抖音"],
        "小红书": [r"xiaohongshu\.com", r"小红书", r"RED\s*书"],
        "知乎": [r"zhihu\.com", r"知乎"],
        "微信": [r"weixin\.qq\.com", r"微信", r"公众号"],
        "Bilibili": [r"bilibili\.com", r"B站", r"哔哩"],
        "百度": [r"baidu\.com", r"百度"],
        "微博": [r"weibo\.com", r"微博"],
        "汽车之家": [r"autohome\.com\.cn", r"汽车之家"],
        "GitHub": [r"github\.com", r"GitHub"],
        # Western platforms
        "YouTube": [r"youtube\.com", r"YouTube"],
        "Reddit": [r"reddit\.com", r"Reddit"],
        "Wikipedia": [r"wikipedia\.org", r"Wikipedia"],
        "LinkedIn": [r"linkedin\.com", r"LinkedIn"],
        "Twitter/X": [r"twitter\.com", r"x\.com", r"Twitter"],
        "Facebook": [r"facebook\.com", r"Facebook"],
        "Instagram": [r"instagram\.com", r"Instagram"],
    }

    all_urls = []
    for result in tavily_result.get("results", []):
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        content = result.get("content", "").lower()
        all_urls.append(url)

        # Check each platform
        for platform, patterns in platform_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url) or re.search(pattern, title):
                    if platform not in analysis["platforms_detected"]:
                        analysis["platforms_detected"].append(platform)
                    if platform not in analysis["platform_details"]:
                        analysis["platform_details"][platform] = {
                            "urls": [],
                            "sample_titles": [],
                        }
                    analysis["platform_details"][platform]["urls"].append(url)
                    analysis["platform_details"][platform]["sample_titles"].append(result.get("title"))
                    break

    # Add summary
    analysis["summary"] = {
        "total_results": len(tavily_result.get("results", [])),
        "platforms_found": len(analysis["platforms_detected"]),
        "platforms": analysis["platforms_detected"],
    }

    return analysis

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def check_youtube_presence(brand_name: str) -> dict:
    """Check brand presence on YouTube."""
    result = {
        "platform": "YouTube",
        "correlation": 0.737,
        "weight": "25%",
        "has_channel": False,
        "mentioned_in_videos": False,
        "search_url": f"https://www.youtube.com/results?search_query={quote_plus(brand_name)}",
        "recommendations": [],
    }

    # Note: Actual YouTube API would be used in production
    # This provides the framework for Claude Code to use WebFetch
    result["check_instructions"] = [
        f"Search YouTube for '{brand_name}' and check:",
        "1. Does the brand have an official YouTube channel?",
        "2. Are there videos FROM the brand (tutorials, demos, thought leadership)?",
        "3. Are there videos ABOUT the brand from other creators?",
        "4. What's the view count on brand-related videos?",
        "5. Are there positive reviews or demonstrations?",
    ]

    result["recommendations"] = [
        "Create a YouTube channel if none exists",
        "Publish educational/tutorial content related to your niche",
        "Encourage customers to create review/demo videos",
        "Optimize video titles and descriptions with brand name",
        "Add timestamps and chapters to improve AI parseability",
        "Include transcripts (YouTube auto-generates, but review for accuracy)",
    ]

    return result


def check_reddit_presence(brand_name: str) -> dict:
    """Check brand presence on Reddit."""
    result = {
        "platform": "Reddit",
        "correlation": "High",
        "weight": "25%",
        "has_subreddit": False,
        "mentioned_in_discussions": False,
        "search_url": f"https://www.reddit.com/search/?q={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"Search Reddit for '{brand_name}' and check:",
        "1. Does the brand have its own subreddit (r/brandname)?",
        "2. Is the brand discussed in relevant industry subreddits?",
        "3. What's the sentiment (positive, negative, neutral)?",
        "4. Are there recommendation threads mentioning the brand?",
        "5. Does the brand have an official Reddit presence?",
        "6. Are mentions recent (within last 6 months)?",
    ]

    result["recommendations"] = [
        "Monitor relevant subreddits for brand mentions",
        "Participate authentically in industry discussions (no spam)",
        "Create an official Reddit account for customer support",
        "Share valuable content (not just self-promotion)",
        "Respond to questions about your product/service category",
        "Reddit authenticity matters — don't use marketing speak",
    ]

    return result


def check_wikipedia_presence(brand_name: str) -> dict:
    """Check brand/entity presence on Wikipedia and Wikidata."""
    result = {
        "platform": "Wikipedia",
        "correlation": "High",
        "weight": "20%",
        "has_wikipedia_page": False,
        "has_wikidata_entry": False,
        "cited_in_articles": False,
        "search_url": f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(brand_name)}",
        "wikidata_url": f"https://www.wikidata.org/w/index.php?search={quote_plus(brand_name)}",
        "recommendations": [],
    }

    # Check Wikipedia API
    try:
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote_plus(brand_name)}&format=json"
        response = requests.get(api_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                # Check if top result is about the brand
                top_title = search_results[0].get("title", "").lower()
                if brand_name.lower() in top_title:
                    result["has_wikipedia_page"] = True
                result["wikipedia_search_results"] = len(search_results)
    except Exception:
        pass

    # Check Wikidata
    try:
        wikidata_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={quote_plus(brand_name)}&language=en&format=json"
        response = requests.get(wikidata_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            entities = data.get("search", [])
            if entities:
                result["has_wikidata_entry"] = True
                result["wikidata_id"] = entities[0].get("id", "")
                result["wikidata_description"] = entities[0].get("description", "")
    except Exception:
        pass

    result["recommendations"] = [
        "If eligible, create a Wikipedia article (requires notability criteria)",
        "Ensure Wikidata entry exists with complete structured data",
        "Add sameAs links in schema markup pointing to Wikipedia/Wikidata",
        "Get cited in existing Wikipedia articles as a source",
        "Build notability through press coverage and independent reviews",
        "Note: Wikipedia has strict notability guidelines — PR coverage helps establish this",
    ]

    return result


def check_linkedin_presence(brand_name: str) -> dict:
    """Check brand presence on LinkedIn."""
    result = {
        "platform": "LinkedIn",
        "correlation": "Moderate",
        "weight": "15%",
        "has_company_page": False,
        "employee_thought_leadership": False,
        "search_url": f"https://www.linkedin.com/search/results/companies/?keywords={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"Search LinkedIn for '{brand_name}' and check:",
        "1. Does the company have a LinkedIn page?",
        "2. How many followers?",
        "3. Is the page active with recent posts?",
        "4. Do employees post thought leadership content?",
        "5. Are there LinkedIn articles about the brand?",
        "6. Is there engagement on posts (likes, comments, shares)?",
    ]

    result["recommendations"] = [
        "Create/optimize LinkedIn company page",
        "Post regular thought leadership content",
        "Encourage employees to share company content",
        "Publish long-form LinkedIn articles",
        "Engage with industry discussions and comments",
        "Add company LinkedIn URL to schema sameAs property",
    ]

    return result


def check_douyin_presence(brand_name: str) -> dict:
    """Check brand presence on Douyin (Chinese TikTok)."""
    result = {
        "platform": "抖音 (Douyin)",
        "correlation": "High",
        "weight": "20%",
        "has_official_account": False,
        "has_live_streaming": False,
        "search_url": f"https://www.douyin.com/search/{quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"在抖音搜索 '{brand_name}' 并检查:",
        "1. 品牌是否有官方账号?",
        "2. 账号的粉丝数量和活跃度?",
        "3. 是否有品牌相关的短视频/直播?",
        "4. 品牌相关内容的点赞、评论、分享量?",
        "5. 是否有人发布产品测评或使用分享?",
    ]

    result["recommendations"] = [
        "注册品牌官方抖音账号",
        "发布产品教程、使用技巧类短视频",
        "与KOC/KOL合作进行产品种草",
        "开通品牌直播间进行直播带货",
        "优化抖音主页SEO，包含关键词",
        "鼓励用户生成内容(UGC)",
    ]

    return result


def check_xiaohongshu_presence(brand_name: str) -> dict:
    """Check brand presence on Xiaohongshu (RED/Little Red Book)."""
    result = {
        "platform": "小红书 (Xiaohongshu/RED)",
        "correlation": "High",
        "weight": "20%",
        "has_official_account": False,
        "notes_posted": 0,
        "search_url": f"https://www.xiaohongshu.com/search_result?keyword={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"在小红书搜索 '{brand_name}' 并检查:",
        "1. 品牌是否有官方账号(企业号)?",
        "2. 相关笔记(帖子)的数量和质量?",
        "3. 笔记的点赞、收藏、评论量?",
        "4. 是否有素人或KOL的真实分享?",
        "5. 品牌关键词下的笔记排名?",
    ]

    result["recommendations"] = [
        "注册小红书企业号",
        "发布真实、有价值的种草笔记",
        "与小红书博主合作进行产品推广",
        "优化笔记标题和内容中的关键词",
        "使用小红书标签增加曝光",
        "鼓励用户分享真实使用体验",
    ]

    return result


def check_zhihu_presence(brand_name: str) -> dict:
    """Check brand presence on Zhihu (Chinese Quora)."""
    result = {
        "platform": "知乎",
        "correlation": "Moderate",
        "weight": "15%",
        "has_official_account": False,
        "has_expert_topics": False,
        "search_url": f"https://www.zhihu.com/search?type=content&q={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"在知乎搜索 '{brand_name}' 并检查:",
        "1. 是否有品牌相关的问题和回答?",
        "2. 品牌是否被收录为话题?",
        "3. 相关内容的专业性和深度?",
        "4. 是否有官方认证账号?",
        "5. 回答的赞同数和关注度?",
    ]

    result["recommendations"] = [
        "注册知乎机构号",
        "在相关问题下发布专业回答",
        "发布品牌相关的深度文章",
        "参与行业话题讨论建立专业形象",
        "与知乎优秀回答者合作",
        "添加品牌链接到网站schema的sameAs中",
    ]

    return result


def check_wechat_presence(brand_name: str) -> dict:
    """Check brand presence on WeChat."""
    result = {
        "platform": "微信 (WeChat)",
        "correlation": "Moderate",
        "weight": "15%",
        "has_official_account": False,
        "articles_published": 0,
        "search_url": f"https://weixin.sogou.com/weixin?type=1&query={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"在微信搜索 '{brand_name}' 并检查:",
        "1. 是否有品牌官方公众号?",
        "2. 公众号的阅读量和关注数?",
        "3. 是否定期发布高质量内容?",
        "4. 文章是否被微信搜狗收录?",
        "5. 是否有小程序或视频号?",
    ]

    result["recommendations"] = [
        "注册微信公众平台账号",
        "定期发布行业相关高质量文章",
        "开通微信视频号与公众号联动",
        "创建品牌小程序提供增值服务",
        "利用微信搜狗SEO优化内容",
        "在文章中添加品牌链接到官网",
    ]

    return result


def check_bilibili_presence(brand_name: str) -> dict:
    """Check brand presence on Bilibili."""
    result = {
        "platform": "哔哩哔哩 (Bilibili)",
        "correlation": "Moderate",
        "weight": "10%",
        "has_official_channel": False,
        "video_count": 0,
        "search_url": f"https://search.bilibili.com/all?keyword={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"在B站搜索 '{brand_name}' 并检查:",
        "1. 品牌是否有官方UP主账号?",
        "2. 相关视频的数量和播放量?",
        "3. 视频弹幕和评论质量?",
        "4. 是否有品牌赞助或合作的视频?",
        "5. 账号的粉丝数和活跃度?",
    ]

    result["recommendations"] = [
        "注册B站官方UP主账号",
        "发布产品测评、技术教程类视频",
        "与B站知名UP主合作推广",
        "利用B站弹幕互动增加参与度",
        "制作年轻人喜欢的内容风格",
        "在视频描述中添加品牌信息和链接",
    ]

    return result


def check_baidu_presence(brand_name: str, domain: str = None) -> dict:
    """Check brand presence on Baidu search and Baidu Zhidao."""
    result = {
        "platform": "百度 (Baidu)",
        "correlation": "Moderate",
        "weight": "10%",
        "has_baidu_zhidao": False,
        "has_baidu_wiki": False,
        "baidu_search_url": f"https://www.baidu.com/s?wd={quote_plus(brand_name)}",
        "baidu_zhidao_url": f"https://zhidao.baidu.com/search?word={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"在百度搜索 '{brand_name}' 并检查:",
        "1. 品牌官网是否在搜索结果第一位?",
        "2. 是否有百度知道相关问答?",
        "3. 是否有百度百科词条?",
        "4. 品牌相关的新闻报道数量?",
        "5. 百度快照是否正常更新?",
    ]

    result["recommendations"] = [
        "确保网站被百度正常收录",
        "创建百度知道问答内容",
        "创建或完善百度百科词条",
        "发布新闻稿到权威新闻媒体",
        "优化百度SEO，包括熊掌号",
        "提交网站到百度搜索资源平台",
    ]

    return result


def check_chinese_other_platforms(brand_name: str) -> dict:
    """Check brand presence on additional Chinese platforms."""
    result = {
        "platform": "其他国内平台",
        "weight": "10%",
        "platforms_checked": {},
        "recommendations": [],
    }

    platforms = {
        "微博 (Weibo)": f"https://s.weibo.com/weibo?q={quote_plus(brand_name)}",
        "豆瓣 (Douban)": f"https://www.douban.com/search?query={quote_plus(brand_name)}",
        "什么值得买 (SMZDM)": f"https://www.smzdm.com/search/j_{quote_plus(brand_name)}",
        "百度贴吧": f"https://tieba.baidu.com/f/search/res?qw={quote_plus(brand_name)}",
        "汽车之家": f"https://www.autohome.com.cn/search#searchText={quote_plus(brand_name)}",
    }

    result["platforms_checked"] = {
        name: {
            "search_url": url,
            "check_instruction": f"在{name}搜索 '{brand_name}'",
        }
        for name, url in platforms.items()
    }

    result["recommendations"] = [
        "微博: 发布品牌动态，参与热搜话题",
        "豆瓣: 创建品牌小组，发布专业内容",
        "什么值得买: 合作发布产品评测和优惠信息",
        "百度贴吧: 在相关贴吧发布有价值的帖子",
        "行业垂直平台: 在汽车之家等平台发布专业内容",
    ]

    return result


def check_other_platforms(brand_name: str) -> dict:
    """Check brand presence on additional Western platforms."""
    result = {
        "platform": "Other Platforms (Western)",
        "weight": "15%",
        "platforms_checked": {},
        "recommendations": [],
    }

    platforms = {
        "Quora": f"https://www.quora.com/search?q={quote_plus(brand_name)}",
        "Stack Overflow": f"https://stackoverflow.com/search?q={quote_plus(brand_name)}",
        "GitHub": f"https://github.com/search?q={quote_plus(brand_name)}",
        "Crunchbase": f"https://www.crunchbase.com/textsearch?q={quote_plus(brand_name)}",
        "Product Hunt": f"https://www.producthunt.com/search?q={quote_plus(brand_name)}",
        "G2": f"https://www.g2.com/search?utf8=&query={quote_plus(brand_name)}",
        "Trustpilot": f"https://www.trustpilot.com/search?query={quote_plus(brand_name)}",
    }

    result["platforms_checked"] = {
        name: {
            "search_url": url,
            "check_instruction": f"Search for '{brand_name}' on {name}",
        }
        for name, url in platforms.items()
    }

    result["recommendations"] = [
        "Maintain profiles on industry-relevant platforms",
        "Respond to questions on Quora and Stack Overflow",
        "Encourage customer reviews on G2 and Trustpilot",
        "Keep Crunchbase profile updated (important for B2B)",
        "Open-source contributions on GitHub boost developer brand authority",
        "Product Hunt launch can generate significant initial buzz",
    ]

    return result


def generate_brand_report(brand_name: str, domain: str = None, use_tavily: bool = True) -> dict:
    """Generate a comprehensive brand mention report.

    Args:
        brand_name: Brand name to analyze
        domain: Optional domain for the brand
        use_tavily: Whether to use Tavily API for enhanced platform detection (default: True)
    """
    report = {
        "brand_name": brand_name,
        "domain": domain,
        "analysis_date": "Generated by GEO-SEO Claude Tool",
        "key_insight": "Brand mentions correlate 3x more strongly with AI visibility than backlinks (Ahrefs Dec 2025, 75K brands). 中国市场: 抖音/小红书对国内AI引用影响重大。",
        "platforms": {},
        "overall_recommendations": [],
    }

    # Try Tavily search for enhanced platform detection
    if use_tavily:
        tavily_search_result = tavily_search(
            brand_name,
            platform_hints=["抖音", "小红书", "知乎", "微信", "B站", "Bilibili", "微博", "百度", "YouTube", "Reddit"]
        )
        report["tavily_search"] = tavily_search_result

        if tavily_search_result.get("available"):
            platform_analysis = analyze_tavily_results_for_platforms(tavily_search_result, brand_name)
            report["platform_analysis"] = platform_analysis

    # Check Western platforms
    report["platforms"]["youtube"] = check_youtube_presence(brand_name)
    report["platforms"]["reddit"] = check_reddit_presence(brand_name)
    report["platforms"]["wikipedia"] = check_wikipedia_presence(brand_name)
    report["platforms"]["linkedin"] = check_linkedin_presence(brand_name)
    report["platforms"]["other_western"] = check_other_platforms(brand_name)

    # Check Chinese platforms
    report["platforms"]["douyin"] = check_douyin_presence(brand_name)
    report["platforms"]["xiaohongshu"] = check_xiaohongshu_presence(brand_name)
    report["platforms"]["zhihu"] = check_zhihu_presence(brand_name)
    report["platforms"]["wechat"] = check_wechat_presence(brand_name)
    report["platforms"]["bilibili"] = check_bilibili_presence(brand_name)
    report["platforms"]["baidu"] = check_baidu_presence(brand_name, domain)
    report["platforms"]["other_chinese"] = check_chinese_other_platforms(brand_name)

    # Overall recommendations
    report["overall_recommendations"] = [
        # Western
        "Priority 1: YouTube — highest correlation (0.737) with AI citations. Create educational content.",
        "Priority 2: Reddit — build authentic presence in industry subreddits. No marketing speak.",
        "Priority 3: Wikipedia — establish notability through press coverage, then create/improve entry.",
        "Priority 4: LinkedIn — thought leadership content from founders and employees.",
        # Chinese
        "【国内】Priority 1: 抖音 — 最高权重(20%)，创建官方账号发布短视频和直播",
        "【国内】Priority 2: 小红书 — 品牌种草核心平台，与KOC/KOL合作至关重要",
        "【国内】Priority 3: 知乎 — 建立专业形象，发布深度问答和文章",
        "【国内】Priority 4: 微信 — 公众号+视频号联动，内容沉淀和传播",
        "【国内】Priority 5: B站 — 年轻用户群体，产品测评和技术教程视频",
        # Cross-platform
        "Cross-platform: Ensure consistent NAP (Name, Address, Phone) across all platforms.",
        "Cross-platform: 国内外平台保持品牌名称和描述一致",
        "Schema markup: Add sameAs property linking to ALL platform profiles.",
        "Schema markup: 在网站JSON-LD中添加sameAs链接到国内外所有平台",
        "Monitor: Set up brand mention alerts across all platforms.",
    ]

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python brand_scanner.py <brand_name> [domain]")
        print("Example: python brand_scanner.py 'Acme Corp' acmecorp.com")
        sys.exit(1)

    brand = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None

    result = generate_brand_report(brand, domain)
    print(json.dumps(result, indent=2, default=str))
