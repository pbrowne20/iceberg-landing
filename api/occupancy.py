from http import HTTPStatus
import json
from analytics.data_loader import load

def handler(request):
    try:
        q, _ = load()
        q_sorted = q.sort_values(["fiscal_year","fiscal_quarter"]).tail(1).iloc[0]
        occ = float(q_sorted["Leased_Percent"])  # expects % already (0-100)
        return (
            json.dumps({"current_occupancy_pct": occ, "units": "%"}),
            HTTPStatus.OK,
            {"Content-Type": "application/json"}
        )
    except Exception as e:
        return (
            json.dumps({"error": str(e)}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"Content-Type": "application/json"}
        )
