import pytest
import sys
sys.path.insert(0, "scripts")
from geo_attribution import (
    estimate_geo_attributed_traffic,
    estimate_geu_influenced_conversions,
    project_geo_roi,
    generate_attribution_report,
)


def test_attribution_returns_expected_keys():
    result = estimate_geo_attributed_traffic(50)
    assert "estimated_monthly_clicks" in result
    assert result["estimated_monthly_clicks"] > 0


def test_roi_calculation():
    result = project_geo_roi(1000, 30, 100)
    assert "roi_percentage" in result
    assert "roi_multiplier" in result


def test_influenced_conversions_higher_than_direct():
    traffic = 1000
    result = estimate_geu_influenced_conversions(traffic)
    assert result["geo_influenced_conversions"] >= result["direct_conversions"]


def test_generate_attribution_report_structure():
    result = generate_attribution_report({}, 50, 500)
    assert "traffic_attribution" in result
    assert "conversion_attribution" in result
    assert "roi_projection" in result
    assert "key_insight" in result


def test_roi_multiplier_calculation():
    """High citations should produce positive ROI."""
    result = project_geo_roi(500, 100, 100)
    assert result["roi_multiplier"] >= 1


def test_zero_investment_handled():
    result = project_geo_roi(0, 50, 100)
    assert result["roi_percentage"] == 0
    assert result["roi_multiplier"] == 0