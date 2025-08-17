from dataclasses import dataclass
import pandas as pd
import re

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def _pick_by_tokens(df: pd.DataFrame, must_tokens=(), any_tokens=()):
    """
    Return the first column whose normalized name contains all must_tokens
    and at least one any_tokens (if provided). Fall back to any that has any_tokens.
    """
    cols = list(df.columns)
    norm = {c: _norm(c) for c in cols}

    # hard prefer: all must_tokens present
    best = [c for c in cols if all(t in norm[c] for t in must_tokens) and (not any_tokens or any(t in norm[c] for t in any_tokens))]
    if best:
        return best[0]

    # fallback: any of any_tokens
    if any_tokens:
        best = [c for c in cols if any(t in norm[c] for t in any_tokens)]
        if best:
            return best[0]

    raise KeyError(f"Could not find a column with tokens must={must_tokens}, any={any_tokens}. Known: {cols}")

def _maybe_sort(df: pd.DataFrame) -> pd.DataFrame:
    cols = { _norm(c): c for c in df.columns }
    year = None
    qtr  = None
    for k in cols:
        if ("fiscal" in k and "year" in k) or k == "year" or k == "fy":
            year = cols[k]
        if ("fiscal" in k and "quart" in k) or k in ("quarter", "qtr"):
            qtr = cols[k]
    if year and qtr:
        return df.sort_values([year, qtr])
    return df

@dataclass
class NOISFSummary:
    current_quarterly_noi_per_kSF: float
    trailing_4q_avg: float
    efficiency_rating: str
    units: str = "$MM per kSF"

def noi_per_sf_summary(q: pd.DataFrame) -> NOISFSummary:
    # NOI — prefer same-store NOI, but accept anything with "noi"
    noi_col = None
    try:
        noi_col = _pick_by_tokens(q, must_tokens=("noi",), any_tokens=("samestore","ss"))
    except Exception:
        noi_col = _pick_by_tokens(q, must_tokens=("noi",))

    # Square feet — prefer rentable, accept rsf/rba/sf/sqft/gla
    try_tok = ("rentable", "rsf", "rba", "squarefeet", "sqft", "sf", "gla")
    sf_col = _pick_by_tokens(q, any_tokens=try_tok)

    q_sorted = _maybe_sort(q)

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
