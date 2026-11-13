from typing import Dict, List, Any

DEFAULT_STAGE_PROBABILITIES = {
    "qualified": 20,
    "meeting": 35,
    "proposal": 60,
    "negotiation": 80,
    "closed_won": 100,
    "closed_lost": 0
}

def get_default_probability(stage: str) -> int:
    return DEFAULT_STAGE_PROBABILITIES.get(stage.lower(), 10)

def compute_weighted_value(value: float, probability: int) -> float:
    return round(value * (probability / 100.0), 2)

def compute_pipeline_metrics(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_val = 0.0
    weighted_val = 0.0
    closed_won_val = 0.0
    active_count = 0
    closed_won_count = 0
    closed_lost_count = 0

    for d in deals:
        stage = d["stage"]
        val = float(d["value"])
        prob = int(d["probability"])
        weighted = compute_weighted_value(val, prob)

        if stage == "closed_won":
            closed_won_val += val
            closed_won_count += 1
        elif stage == "closed_lost":
            closed_lost_count += 1
        else:
            total_val += val
            weighted_val += weighted
            active_count += 1

    total_closed = closed_won_count + closed_lost_count
    win_rate = round((closed_won_count / total_closed * 100.0), 1) if total_closed > 0 else 0.0

    return {
        "total_pipeline_value": round(total_val, 2),
        "weighted_pipeline_value": round(weighted_val, 2),
        "closed_won_value": round(closed_won_val, 2),
        "total_active_deals": active_count,
        "win_rate_pct": win_rate
    }
