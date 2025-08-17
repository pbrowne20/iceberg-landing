from http.server import BaseHTTPRequestHandler
import json, re
from analytics.data_loader import load

def _pick(df, preferred_names, patterns):
    # exact
    for n in preferred_names:
        if n in df.columns:
            return n
    # case-insensitive exact
    lower = {c.lower(): c for c in df.columns}
    for n in preferred_names:
        if n.lower() in lower:
            return lower[n.lower()]
    # regex match
    regs = [re.compile(p, re.I) for p in patterns]
    for c in df.columns:
        if any(r.search(c) for r in regs):
            return c
    raise KeyError(f"Could not find any of {preferred_names} / {patterns} in {list(df.columns)}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q, _ = load()

            # Try to sort by year/quarter; if not found, just use file order.
            try:
                year_col = _pick(q,
                    ["fiscal_year","Fiscal_Year","Fiscal Year","Year","year"],
                    [r"fiscal.*year", r"^year$"]
                )
                qtr_col = _pick(q,
                    ["fiscal_quarter","Fiscal_Quarter","Fiscal Quarter","Quarter","Qtr","quarter","qtr"],
                    [r"fiscal.*quart", r"\bq(tr)?\b", r"\bquarter\b"]
                )
                q = q.sort_values([year_col, qtr_col])
            except Exception:
                pass

            leased_col = _pick(q,
                ["Leased_Percent","Leased %","Leased_Pct","LeasedPercent","Occupancy","Occupancy %","OccupancyPercent"],
                [r"leased.*(percent|pct|%)", r"\boccup"]
            )

            cur = q.tail(1).iloc[0]
            occ = float(cur[leased_col])

            # If your CSV stores occupancy as 0.95 instead of 95.0, uncomment next line:
            # if occ <= 1.0: occ *= 100.0

            body = {"current_occupancy_pct": occ, "units": "%", "column_used": leased_col}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
