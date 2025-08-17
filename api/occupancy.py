from http.server import BaseHTTPRequestHandler
import json
from analytics.data_loader import load
from analytics.columns import resolve  # if you've placed columns.py in analytics/

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q, _ = load()
            occ_col = resolve(q, "Leased_Percent", domain="quarterly")
            cur = q.sort_values(["fiscal_year","fiscal_quarter"]).tail(1).iloc[0]
            occ = float(cur[occ_col])
            # If your occupancy is 0.95 instead of 95.0, uncomment the next line:
            # if occ <= 1.0: occ *= 100.0

            body = json.dumps({"current_occupancy_pct": occ, "units": "%"})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
