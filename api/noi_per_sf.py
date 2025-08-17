from http.server import BaseHTTPRequestHandler
import json
from analytics.data_loader import load
from analytics.financial_metrics import noi_per_sf_summary

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q, _ = load()
            s = noi_per_sf_summary(q)
            body = json.dumps(s.__dict__)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
