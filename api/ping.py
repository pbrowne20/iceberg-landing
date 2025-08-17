from http import HTTPStatus
import json

def handler(request):
    return (json.dumps({"ok": True, "msg": "pong"}), HTTPStatus.OK, {"Content-Type": "application/json"})
