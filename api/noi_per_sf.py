from http import HTTPStatus
import json
from analytics.data_loader import load
from analytics.financial_metrics import noi_per_sf_summary

def handler(request):
    try:
        q, _ = load()
        s = noi_per_sf_summary(q)
        return (
            json.dumps(s.__dict__),
            HTTPStatus.OK,
            {"Content-Type": "application/json"}
        )
    except Exception as e:
        return (
            json.dumps({"error": str(e)}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"Content-Type": "application/json"}
        )
