from http.server import BaseHTTPRequestHandler
import json, re
from analytics.data_loader import load
import pandas as pd

def _norm(s: str) -> str:
    # lower-case and remove non-letters/numbers so "Leased %" -> "leased"
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def _best_occupancy_col(df: pd.DataFrame) -> str:
    # 1) name-based candidates
    prefer_tokens = ("leased", "occup", "occ")
    bonus_tokens  = ("pct", "percent", "%")
    candidates = []
    for c in df.columns:
        n = _norm(c)
        score = 0
        if any(t in n for t in prefer_tokens):
            score += 2
        if any(t in n for t in bonus_tokens):
            score += 1
        # keep only numeric-ish columns
        try:
            float(df[c].tail(1).iloc[0])
            candidates.append((score, c))
        except Exception:
            pass

    # 2) if nothing by name, try any numeric %-looking column
    if not candidates:
        for c in df.columns:
            try:
                v = float(df[c].tail(1).iloc[0])
                if (0 <= v <= 1) or (0 <= v <= 100):
                    candidates.append((1, c))
            except Exception:
                continue

    if not candidates:
        raise KeyError(f"No numeric occupancy-like column found. Known columns: {list(df.columns)}")

    # choose the highest score; break ties by last column (usually latest metric)
    candidates.sort(key=lambda x: (x[0], list(df.columns).index(x[1])))
    return candidates[-1][1]

def _maybe_sort(df: pd.DataFrame) -> pd.DataFrame:
    # Try to sort by year/quarter if present; otherwise return as-is
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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q, _ = load()
            q = _maybe_sort(q)
            col = _best_occupancy_col(q)
            val = float(q.tail(1).iloc[0][col])

            # If your data is 0–1 (e.g., 0.95), convert to percent:
            if val <= 1.0:
                val *= 100.0

            body = {"current_occupancy_pct": val, "units": "%", "column_used": col}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
