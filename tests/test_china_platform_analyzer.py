import pytest
import sys
sys.path.insert(0, "scripts")
from china_platform_analyzer import analyze_china_platform_readiness, _get_chinese_char_ratio


def test_china_platform_returns_structure():
    html = "<html><body><p>Some English content here.</p></body></html>"
    result = analyze_china_platform_readiness(html)
    assert "baidu_wenxin_score" in result
    assert "alibaba_tongyi_score" in result
    assert "bytedance_douai_score" in result
    assert "composite_china_score" in result
    assert "recommendations" in result


def test_chinese_char_ratio_english():
    text = "Hello world, this is a test."
    ratio = _get_chinese_char_ratio(text)
    assert ratio == 0.0


def test_chinese_char_ratio_chinese():
    text = "这是一个中文测试内容"
    ratio = _get_chinese_char_ratio(text)
    assert ratio == 1.0


def test_chinese_char_ratio_mixed():
    text = "Hello 世界"
    ratio = _get_chinese_char_ratio(text)
    assert 0 < ratio < 1


def test_video_boosts_douai_score():
    html_with_video = "<html><body><video src='test.mp4'></video><p>Some content.</p></body></html>"
    html_without = "<html><body><p>Some content.</p></body></html>"
    result_with = analyze_china_platform_readiness(html_with_video)
    result_without = analyze_china_platform_readiness(html_without)
    assert result_with["bytedance_douai_score"] >= result_without["bytedance_douai_score"]