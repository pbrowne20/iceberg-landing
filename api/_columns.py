from http.server import BaseHTTPRequestHandler
import json
from analytics.data_loader import load

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q, g = load()
            out = {
                "quarterly_columns": list(q.columns),
                "geographic_columns": list(g.columns),
                "quarterly_preview": q.head(3).to_dict(orient="records"),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(out, default=str, indent=2).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
