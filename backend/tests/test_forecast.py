import pytest
from app.engine.forecast import get_default_probability, compute_weighted_value, compute_pipeline_metrics

def test_stage_probabilities():
    assert get_default_probability("qualified") == 20
    assert get_default_probability("meeting") == 35
    assert get_default_probability("proposal") == 60
    assert get_default_probability("negotiation") == 80
    assert get_default_probability("closed_won") == 100
    assert get_default_probability("closed_lost") == 0
    assert get_default_probability("unknown_stage") == 10

def test_weighted_value():
    assert compute_weighted_value(100000.0, 50) == 50000.0
    assert compute_weighted_value(75000.0, 0) == 0.0
    assert compute_weighted_value(120000.0, 100) == 120000.0
    assert compute_weighted_value(45000.0, 35) == 15750.0

def test_pipeline_metrics_empty():
    metrics = compute_pipeline_metrics([])
    assert metrics["total_pipeline_value"] == 0.0
    assert metrics["weighted_pipeline_value"] == 0.0
    assert metrics["closed_won_value"] == 0.0
    assert metrics["total_active_deals"] == 0
    assert metrics["win_rate_pct"] == 0.0

def test_pipeline_metrics_calculation():
    deals = [
        {"value": 100000.0, "stage": "proposal", "probability": 60},      # Active: 100k, weighted: 60k
        {"value": 50000.0, "stage": "negotiation", "probability": 80},    # Active: 50k, weighted: 40k
        {"value": 30000.0, "stage": "closed_won", "probability": 100},    # Won: 30k
        {"value": 20000.0, "stage": "closed_lost", "probability": 0},     # Lost: 20k
    ]
    metrics = compute_pipeline_metrics(deals)
    assert metrics["total_pipeline_value"] == 150000.0
    assert metrics["weighted_pipeline_value"] == 100000.0
    assert metrics["closed_won_value"] == 30000.0
    assert metrics["total_active_deals"] == 2
    # Resolved: 1 won, 1 lost => 50% win rate
    assert metrics["win_rate_pct"] == 50.0
