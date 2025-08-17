from dataclasses import dataclass
import pandas as pd
from .columns import resolve  # <-- add this import

@dataclass
class NOISFSummary:
    current_quarterly_noi_per_kSF: float
    trailing_4q_avg: float
    efficiency_rating: str
    units: str = "$MM per kSF"

def noi_per_sf_summary(q: pd.DataFrame) -> NOISFSummary:
    # Resolve columns against your CSV headers
    noi_col   = resolve(q, "Same_Store_Net_Operating_Income", domain="quarterly")
    sf_col    = resolve(q, "Rentable_SF", domain="quarterly")
    year_col  = resolve(q, "fiscal_year", domain="quarterly")
    qtr_col   = resolve(q, "fiscal_quarter", domain="quarterly")

    q_sorted = q.sort_values([year_col, qtr_col])
    cur = q_sorted.tail(1)
    cur_noi_mm = cur[noi_col].iloc[0] / 1e6
    cur_sf_k   = cur[sf_col].iloc[0] / 1e3
    cur_ratio  = cur_noi_mm / cur_sf_k

    t4 = q_sorted.tail(4)
    t4_noi_mm = t4[noi_col].sum() / 1e6
    t4_sf_k   = t4[sf_col].sum() / 1e3
    t4_ratio  = t4_noi_mm / t4_sf_k

    rating = "strong" if cur_ratio >= t4_ratio else "mixed"
    return NOISFSummary(cur_ratio, t4_ratio, rating)
