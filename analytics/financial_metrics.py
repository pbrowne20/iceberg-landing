from dataclasses import dataclass
import pandas as pd

@dataclass
class NOISFSummary:
    current_quarterly_noi_per_kSF: float
    trailing_4q_avg: float
    efficiency_rating: str
    units: str = "$MM per kSF"

def noi_per_sf_summary(q: pd.DataFrame) -> NOISFSummary:
    # Adjust these names or plug in your alias resolver as needed
    noi_col = "Same_Store_Net_Operating_Income"
    sf_col  = "Rentable_SF"
    q_sorted = q.sort_values(["fiscal_year","fiscal_quarter"])
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
