from dataclasses import dataclass
import pandas as pd
import re

def _pick(df, preferred_names, patterns):
    # exact
    for n in preferred_names:
        if n in df.columns:
            return n
    # case-insensitive
    lower = {c.lower(): c for c in df.columns}
    for n in preferred_names:
        if n.lower() in lower:
            return lower[n.lower()]
    # regex
    regs = [re.compile(p, re.I) for p in patterns]
    for c in df.columns:
        if any(r.search(c) for r in regs):
            return c
    raise KeyError(f"Could not find any of {preferred_names} / {patterns} in {list(df.columns)}")

@dataclass
class NOISFSummary:
    current_quarterly_noi_per_kSF: float
    trailing_4q_avg: float
    efficiency_rating: str
    units: str = "$MM per kSF"

def noi_per_sf_summary(q: pd.DataFrame) -> NOISFSummary:
    noi_col = _pick(q,
        ["Same_Store_Net_Operating_Income","SSNOI","SameStoreNOI","ss_noi","ssnoi_cash"],
        [r"(same|ss).*store.*noi", r"\bnoi\b"]
    )
    sf_col = _pick(q,
        ["Rentable_SF","Rentable SF","Total_SF","Total SF","Square_Feet","SF"],
        [r"rentable.*(sf|sq|square)", r"(total|rentable).*(sf|sq|square)"]
    )

    # Sort if we can find year/quarter; otherwise use file order
    try:
        year_col = _pick(q,
            ["fiscal_year","Fiscal_Year","Fiscal Year","Year","year"],
            [r"fiscal.*year", r"^year$"]
        )
        qtr_col = _pick(q,
            ["fiscal_quarter","Fiscal_Quarter","Fiscal Quarter","Quarter","Qtr","quarter","qtr"],
            [r"fiscal.*quart", r"\bq(tr)?\b", r"\bquarter\b"]
        )
        q_sorted = q.sort_values([year_col, qtr_col])
    except Exception:
        q_sorted = q

    cur = q_sorted.tail(1)
    cur_noi_mm = float(cur[noi_col].iloc[0]) / 1e6
    cur_sf_k   = float(cur[sf_col].iloc[0]) / 1e3
    cur_ratio  = cur_noi_mm / cur_sf_k

    t4 = q_sorted.tail(4)
    t4_noi_mm = float(t4[noi_col].sum()) / 1e6
    t4_sf_k   = float(t4[sf_col].sum()) / 1e3
    t4_ratio  = t4_noi_mm / t4_sf_k

    rating = "strong" if cur_ratio >= t4_ratio else "mixed"
    return NOISFSummary(cur_ratio, t4_ratio, rating)
