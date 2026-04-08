import pytest
import sys
sys.path.insert(0, "scripts")
from citability_scorer import score_passage


def test_score_passage_returns_dict():
    result = score_passage("Gemini is an AI model developed by Google.")
    assert isinstance(result, dict)
    assert "total_score" in result
    assert 0 <= result["total_score"] <= 100


def test_score_passage_statistics_boost():
    """Statistics should increase score significantly."""
    no_stats = score_passage("Content marketing is important for brands.")
    with_stats = score_passage("Content marketing delivers 3.5x more leads than traditional marketing, with 93% of companies reporting increased engagement.")
    assert with_stats["total_score"] > no_stats["total_score"]


def test_score_passage_answer_block_pattern():
    """Definition patterns should boost answer block quality."""
    result = score_passage("GEO means Generative Engine Optimization — a strategy for improving AI visibility.")
    assert result["breakdown"]["answer_block_quality"] > 0
