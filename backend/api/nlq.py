# backend/api/nlq.py
from http.server import BaseHTTPRequestHandler
import json, os, traceback
from openai import OpenAI
from analytics.registry import REGISTRY

SYSTEM_PROMPT = """You are the ICEBERG NL router. Use ONLY intents in REGISTRY.
Return STRICT JSON: {"intent": <string>, "args": <object>, "confidence": 0..1, "reasoning": <short string>}
"""

def _allowed_intents():
    return list(REGISTRY.keys())

def _user_prompt(q: str) -> str:
    return f"""User question: {q}

Available intents:
{json.dumps(_allowed_intents())}

Arg specs:
- noi_per_sf_summary: no args.

Return ONLY the JSON.
"""

def _call_openai(text: str) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role":"system","content":SYSTEM_PROMPT},
                  {"role":"user","content":text}],
        temperature=0
    )
    return resp.choices[0].message.content

def _execute_intent(intent: str, args: dict):
    spec = REGISTRY[intent]
    result = spec.fn(args)
    code = (
        f"# Executed plan\n"
        f"from analytics.registry import REGISTRY\n"
        f"result = REGISTRY['{intent}'].fn({args})\n"
    )
    payload = result.__dict__ if hasattr(result, "__dict__") else (result if isinstance(result, dict) else {"value": result})
    return payload, code, spec.units, spec.description

def _format_answer(intent: str, result: dict, units: dict, desc: str) -> str:
    if intent == "noi_per_sf_summary":
        u = units.get("current_quarterly_noi_per_kSF", "")
        return (f"Current NOI per kSF is {result['current_quarterly_noi_per_kSF']:.3f} {u}, "
                f"vs {result['trailing_4q_avg']:.3f} {u} (T4Q). "
                f"Efficiency rating: {result['efficiency_rating']}.")
    return f"{intent} computed. See result."

class handler(BaseHTTPRequestHandler):
    # ---- CORS helpers (this is the important part) ----
    def _cors(self):
        # For tight security, replace "*" with your site origin:
        # e.g., "https://www.icebergre.ai"
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Vary", "Origin")

    def do_OPTIONS(self):
        # Handles the browser preflight for POST requests
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # ---- JSON response helper ----
    def _json(self, code: int, body: dict):
        self.send_response(code)
        self._cors()  # add CORS headers on responses too
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    # ---- Health check (optional GET) ----
    def do_GET(self):
        return self._json(200, {"ok": True, "expects": "POST { q: 'your question' }"})

    # ---- Main NLQ endpoint ----
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(raw or "{}")
            q = (data.get("q") or "").strip()
            if not q:
                return self._json(400, {"error": "missing 'q'"})

            plan_raw = _call_openai(_user_prompt(q))
            plan = json.loads(plan_raw)
            intent = plan.get("intent")
            conf = float(plan.get("confidence", 0))

            if intent not in REGISTRY:
                return self._json(400, {
                    "error":"unsupported_intent",
                    "available_intents": _allowed_intents(),
                    "plan": plan
                })
            if conf < 0.4:
                return self._json(200, {
                    "error":"low_confidence",
                    "available_intents": _allowed_intents(),
                    "plan": plan
                })

            result, code, units, desc = _execute_intent(intent, plan.get("args", {}))
            answer = _format_answer(intent, result, units, desc)
            return self._json(200, {
                "answer": answer,
                "intent": intent,
                "args": plan.get("args", {}),
                "confidence": conf,
                "code": code,
                "result": result,
                "units": units
            })
        except Exception as e:
            return self._json(500, {"error": str(e), "trace": traceback.format_exc()})
