import os, json, traceback
from http import HTTPStatus
from typing import Any, Dict
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

def _execute_intent(intent: str, args: Dict[str, Any]):
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

def _format_answer(intent: str, result: Dict[str, Any], units: Dict[str, str], desc: str) -> str:
    if intent == "noi_per_sf_summary":
        cur = result["current_quarterly_noi_per_kSF"]
        t4 = result["trailing_4q_avg"]
        rating = result["efficiency_rating"]
        u = units.get("current_quarterly_noi_per_kSF", "")
        return f"Current NOI per kSF is {cur:.3f} {u}, vs {t4:.3f} {u} (T4Q). Efficiency rating: {rating}."
    return f"{intent} computed. See result."

def handler(request):
    try:
        body = request.get("body", b"")
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8")
        data = json.loads(body or "{}")
        question = (data.get("q") or "").strip()
        if not question:
            return (json.dumps({"error":"missing 'q'"}), HTTPStatus.BAD_REQUEST, {"Content-Type":"application/json"})

        raw = _call_openai(_user_prompt(question))
        plan = json.loads(raw)

        intent = plan.get("intent")
        confidence = float(plan.get("confidence", 0))
        if intent not in REGISTRY:
            return (json.dumps({
                "error":"unsupported_intent",
                "message": f"Intent '{intent}' is not available.",
                "available_intents": _allowed_intents(),
                "plan": plan
            }), HTTPStatus.BAD_REQUEST, {"Content-Type":"application/json"})

        if confidence < 0.4:
            return (json.dumps({
                "error":"low_confidence",
                "message":"I’m not confident about the mapping. Try rephrasing or pick one of these intents.",
                "available_intents": _allowed_intents(),
                "plan": plan
            }), HTTPStatus.OK, {"Content-Type":"application/json"})

        result, code, units, desc = _execute_intent(intent, plan.get("args", {}))
        answer = _format_answer(intent, result, units, desc)
        return (json.dumps({
            "answer": answer,
            "intent": intent,
            "args": plan.get("args", {}),
            "confidence": confidence,
            "code": code,
            "result": result,
            "units": units
        }), HTTPStatus.OK, {"Content-Type":"application/json"})
    except Exception as e:
        return (json.dumps({"error": str(e), "trace": traceback.format_exc()}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"Content-Type":"application/json"})
