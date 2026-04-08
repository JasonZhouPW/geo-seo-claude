import pytest
import sys
sys.path.insert(0, "scripts")
from scoring import (
    compute_citability_score, compute_eeat_score,
    compute_geu_dimension_scores, normalize_platform_scores,
    compute_final_geu_score, WEIGHTS
)


def test_weights_sum_to_one():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 0.001, f"Weights must sum to 1.0, got {total}"


def test_compute_citability_score_basic():
    score = compute_citability_score(70, 150, False, False)
    assert 0 <= score <= 100


def test_compute_citability_score_with_stats():
    """Statistics should increase score."""
    with_stats = compute_citability_score(70, 150, True, False)
    without = compute_citability_score(70, 150, False, False)
    assert with_stats > without


def test_compute_citability_score_optimal_length():
    """134-167 word range should get bonus."""
    optimal = compute_citability_score(70, 150, False, False)
    short = compute_citability_score(70, 50, False, False)
    assert optimal > short


def test_compute_eeat_score():
    score = compute_eeat_score(experience=50, expertise=80, authority=70, trustworthiness=90)
    assert 0 <= score <= 100


def test_compute_geu_dimension_scores():
    dims = [
        {"dimension": "clarity", "score": 80, "weight": 1.0},
        {"dimension": "accuracy", "score": 90, "weight": 1.0},
    ]
    result = compute_geu_dimension_scores(dims)
    assert result["geu_composite"] == 85.0


def test_normalize_platform_scores():
    scores = {"chatgpt": 120, "perplexity": -10, "gemini": 85}
    normalized = normalize_platform_scores(scores)
    assert normalized["chatgpt"] == 100
    assert normalized["perplexity"] == 0
    assert normalized["gemini"] == 85


def test_compute_final_geu_score():
    result = compute_final_geu_score(
        citability=80, brand=70, content=75,
        technical=90, structured=60,
        platform={"chatgpt": 75, "perplexity": 80}
    )
    assert "composite_score" in result
    assert "breakdown" in result
    assert abs(result["composite_score"] - (
        0.25 * 80 + 0.20 * 70 + 0.20 * 75 +
        0.15 * 90 + 0.10 * 60 + 0.10 * 77.5
    )) < 0.5
