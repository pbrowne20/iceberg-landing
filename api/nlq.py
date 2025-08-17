import os, json, traceback
from http.server import BaseHTTPRequestHandler
from analytics.registry import REGISTRY

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are the ICEBERG NL router. You ONLY plan analytics available in the REGISTRY.
Closed-book rules:
- Use ONLY intents from the provided list.
- If user asks for something outside the registry, propose the closest matching intent.
- Return STRICT JSON: {"intent": <string>, "args": <object>, "confidence": 0..1, "reasoning": <short string>}
Do not include code blocks, extra keys, or text outside JSON.
"""

def _allowed_intents():
    return list(REGISTRY.keys())

def _user_prompt(q: str) -> str:
    return f"""User question: {q}

Available intents:
{json.dumps(_allowed_intents())}

Arg specs (human summary):
- noi_per_sf_summary: no args.

Return ONLY the JSON.
"""

def _call_openai(text: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role":"system","content":SYSTEM_PROMPT},
                  {"role":"user","content":text}],
        temperature=0
    )
    return resp.choices[0].message.content

def _execute_intent(intent: str, args: dict):
    spec = REGISTRY[intent]
    result = spec.fn(args)
    exec_code = f"# Executed plan\nfrom analytics.registry import REGISTRY\nspec = REGISTRY['{intent}']\nresult = spec.fn({args})\n"
    if hasattr(result, "__dict__"):
        payload = result.__dict__
    elif isinstance(result, dict):
        payload = result
    else:
        payload = {"value": result}
    return payload, exec_code, spec.units, spec.description

def _format_answer(intent: str, result: dict, units: dict, desc: str) -> str:
    if intent == "noi_per_sf_summary":
        cur = result["current_quarterly_noi_per_kSF"]
        t4 = result["trailing_4q_avg"]
        rating = result["efficiency_rating"]
        u = units.get("current_quarterly_noi_per_kSF", "")
        return f"Current NOI per kSF is {cur:.3f} {u}, vs {t4:.3f} {u} (T4Q). Efficiency rating: {rating}."
    return f"{intent} computed. See result."

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body or "{}")
            question = (data.get("q") or "").strip()
            
            if not question:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "missing 'q'"}).encode("utf-8"))
                return

            raw = _call_openai(_user_prompt(question))
            plan = json.loads(raw)

            intent = plan.get("intent")
            confidence = float(plan.get("confidence", 0))
            
            if intent not in REGISTRY:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "unsupported_intent",
                    "message": f"Intent '{intent}' is not available.",
                    "available_intents": _allowed_intents(),
                    "plan": plan
                }).encode("utf-8"))
                return

            if confidence < 0.4:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "low_confidence",
                    "message": "I'm not confident about the mapping. Try rephrasing or pick one of these intents.",
                    "available_intents": _allowed_intents(),
                    "plan": plan
                }).encode("utf-8"))
                return

            result, code, units, desc = _execute_intent(intent, plan.get("args", {}))
            answer = _format_answer(intent, result, units, desc)
            
            response_data = {
                "answer": answer,
                "intent": intent,
                "args": plan.get("args", {}),
                "confidence": confidence,
                "code": code,
                "result": result,
                "units": units
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e), 
                "trace": traceback.format_exc()
            }).encode("utf-8"))