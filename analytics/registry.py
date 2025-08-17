from typing import Callable, Dict, Any
from dataclasses import dataclass
from .data_loader import load
from .financial_metrics import noi_per_sf_summary

@dataclass
class MetricSpec:
    fn: Callable[..., Any]
    args: Dict[str, Any]
    returns: str
    units: Dict[str, str]
    description: str

def _require_loaded():
    q, g = load()
    return q, g

def metric_noi_per_sf(_ctx: dict):
    q, _ = _require_loaded()
    return noi_per_sf_summary(q)

REGISTRY: Dict[str, MetricSpec] = {
    "noi_per_sf_summary": MetricSpec(
        fn=metric_noi_per_sf,
        args={},  # no args
        returns="NOISFSummary",
        units={
            "current_quarterly_noi_per_kSF": "$MM/kSF",
            "trailing_4q_avg": "$MM/kSF"
        },
        description="Current and trailing-4Q NOI per thousand SF and an efficiency rating."
    ),
}
