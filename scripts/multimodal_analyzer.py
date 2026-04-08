#!/usr/bin/env python3
"""
Multimodal Content Analyzer — Analyzes image, video, and audio content for AI visibility.
Detects: alt text coverage, video captions/subtitles, chart accessibility, audio transcripts.
"""

import sys
import re
from typing import Dict, List

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed.")
    sys.exit(1)


def analyze_images(soup: BeautifulSoup) -> Dict:
    """Analyze all images for alt text coverage.

    Returns:
        Dict with: total_images, images_with_alt, alt_coverage_pct,
        images_missing_alt (list of src), quality_score (0-100)
    """
    images = soup.find_all("img")
    if not images:
        return {"total_images": 0, "alt_coverage_pct": 0, "quality_score": 0}

    with_alt = []
    without_alt = []

    for img in images:
        alt = img.get("alt", "").strip()
        src = img.get("src", "")
        if alt:
            with_alt.append({"src": src, "alt": alt, "alt_length": len(alt)})
        else:
            without_alt.append({"src": src})

    total = len(images)
    coverage_pct = (len(with_alt) / total * 100) if total > 0 else 0

    quality = 0
    if with_alt:
        avg_len = sum(i["alt_length"] for i in with_alt) / len(with_alt)
        good_alt_count = sum(1 for i in with_alt if 20 <= i["alt_length"] <= 200)
        quality = (good_alt_count / len(with_alt) * 50) + (min(avg_len / 150, 1) * 50)

    return {
        "total_images": total,
        "images_with_alt": len(with_alt),
        "images_missing_alt": len(without_alt),
        "missing_alt_details": without_alt[:5],
        "alt_coverage_pct": round(coverage_pct, 1),
        "quality_score": round(min(100, quality), 1),
    }


def analyze_video_content(soup: BeautifulSoup) -> Dict:
    """Analyze video content for AI index readiness."""
    results = {
        "youtube_videos": [],
        "native_videos": [],
        "videos_with_captions": 0,
        "videos_without_captions": 0,
        "video_readiness_score": 0,
    }

    youtube_embeds = soup.find_all("iframe", src=re.compile(r"youtube\.com|youtu\.be"))
    for embed in youtube_embeds:
        src = embed.get("src", "")
        vid_match = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]+)", src)
        video_id = vid_match.group(1) if vid_match else "unknown"
        results["youtube_videos"].append({
            "video_id": video_id,
            "embed_url": src,
            "has_caption_support": True,
        })

    video_tags = soup.find_all("video")
    for tag in video_tags:
        has_caption = bool(tag.find("track", {"kind": "captions"}))
        results["native_videos"].append({
            "src": tag.get("src", ""),
            "has_caption_track": has_caption,
        })

    total_videos = len(results["youtube_videos"]) + len(results["native_videos"])
    if total_videos > 0:
        native_without = sum(1 for v in results["native_videos"] if not v["has_caption_track"])
        results["videos_without_captions"] = native_without
        results["video_readiness_score"] = round(max(0, 100 - native_without * 20), 1)

    return results


def analyze_charts_and_infographics(soup: BeautifulSoup) -> Dict:
    """Analyze charts, infographics, and data visualizations for AI parseability."""
    figures = soup.find_all("figure")
    svgs = soup.find_all("svg")
    tables = soup.find_all("table")

    figures_with_captions = sum(1 for f in figures if f.find("figcaption"))
    svgs_with_labels = sum(1 for s in svgs if s.get("aria-label") or s.get("role") == "img")

    chart_score = 0
    if figures_with_captions > 0:
        chart_score += min(40, figures_with_captions * 10)
    if svgs_with_labels > 0:
        chart_score += min(30, svgs_with_labels * 15)
    if len(tables) > 0:
        chart_score += min(30, len(tables) * 10)

    return {
        "total_figures": len(figures),
        "figures_with_captions": figures_with_captions,
        "total_svgs": len(svgs),
        "svgs_with_accessibility_labels": svgs_with_labels,
        "total_tables": len(tables),
        "chart_accessibility_score": round(min(100, chart_score), 1),
    }


def analyze_audio_content(soup: BeautifulSoup) -> Dict:
    """Analyze audio content for transcript availability."""
    audio_tags = soup.find_all("audio")
    podcast_episodes = []

    for audio in audio_tags:
        src = audio.get("src", "")
        parent = audio.find_parent()
        transcript_link = None
        if parent:
            links = parent.find_all("a", href=re.compile(r"transcript|文字稿|稿子"))
            if links:
                transcript_link = links[0].get("href")

        podcast_episodes.append({
            "src": src,
            "has_transcript_link": bool(transcript_link),
            "transcript_url": transcript_link,
        })

    total_audio = len(audio_tags)
    with_transcript = sum(1 for p in podcast_episodes if p["has_transcript_link"])

    return {
        "total_audio_elements": total_audio,
        "audio_with_transcripts": with_transcript,
        "audio_transcript_coverage_pct": round(
            with_transcript / total_audio * 100, 1
        ) if total_audio > 0 else 100,
        "episodes": podcast_episodes,
    }


def analyze_multimodal(html_content: str) -> Dict:
    """Run full multimodal analysis on HTML content."""
    soup = BeautifulSoup(html_content, "lxml")

    image_analysis = analyze_images(soup)
    video_analysis = analyze_video_content(soup)
    chart_analysis = analyze_charts_and_infographics(soup)
    audio_analysis = analyze_audio_content(soup)

    image_weight = 0.35
    video_weight = 0.25
    chart_weight = 0.25
    audio_weight = 0.15

    composite = (
        image_analysis["alt_coverage_pct"] * image_weight * 0.4 +
        image_analysis["quality_score"] * image_weight * 0.6 +
        video_analysis["video_readiness_score"] * video_weight +
        chart_analysis["chart_accessibility_score"] * chart_weight +
        audio_analysis["audio_transcript_coverage_pct"] * audio_weight
    )

    return {
        "multimodal_composite_score": round(composite, 1),
        "image_analysis": image_analysis,
        "video_analysis": video_analysis,
        "chart_analysis": chart_analysis,
        "audio_analysis": audio_analysis,
        "recommendations": _generate_multimodal_recommendations(
            image_analysis, video_analysis, chart_analysis, audio_analysis
        ),
    }


def _generate_multimodal_recommendations(
    image: Dict, video: Dict, chart: Dict, audio: Dict
) -> List[str]:
    recs = []
    if image["alt_coverage_pct"] < 80:
        recs.append(f"Add descriptive alt text to {image['images_missing_alt']} images "
                     f"(current coverage: {image['alt_coverage_pct']}%)")
    if image["quality_score"] < 60:
        recs.append("Improve alt text quality — aim for 40-150 character descriptive alt text")
    if video["videos_without_captions"] > 0:
        recs.append(f"Add caption tracks to {video['videos_without_captions']} native videos")
    if chart["figures_with_captions"] < chart["total_figures"] * 0.5:
        recs.append("Add <figcaption> to at least 50% of figures and charts")
    if audio["audio_transcript_coverage_pct"] < 50:
        recs.append("Add text transcripts for audio/podcast content")
    return recs


if __name__ == "__main__":
    import json
    if len(sys.argv) < 2:
        print("Usage: python multimodal_analyzer.py <html_file_or_url>")
        sys.exit(1)

    url_or_file = sys.argv[1]
    if url_or_file.startswith("http"):
        import requests
        resp = requests.get(url_or_file, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        html = resp.text
    else:
        with open(url_or_file) as f:
            html = f.read()

    result = analyze_multimodal(html)
    print(json.dumps(result, indent=2, ensure_ascii=False))
