from http.server import BaseHTTPRequestHandler
import json
from analytics.data_loader import load
from analytics.columns import resolve  # <-- use the alias resolver

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q, _ = load()
            # Resolve the right column names based on your CSV
            year_col   = resolve(q, "fiscal_year", domain="quarterly")
            qtr_col    = resolve(q, "fiscal_quarter", domain="quarterly")
            leased_col = resolve(q, "Leased_Percent", domain="quarterly")

            cur = q.sort_values([year_col, qtr_col]).tail(1).iloc[0]
            occ = float(cur[leased_col])

            # If your occupancy is stored 0–1 instead of 0–100, uncomment this:
            # if occ <= 1.0: occ *= 100.0

            body = {"current_occupancy_pct": occ, "units": "%"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
