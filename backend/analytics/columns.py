
"""
Column alias resolver for ICEBERG.
Usage:
    from columns import resolve
    col = resolve(df, "Same_Store_Net_Operating_Income", domain="quarterly")
"""
from typing import Dict
import pandas as pd

ALIAS_MAP = {
  "quarterly": {
    "fiscal_year": [],
    "fiscal_quarter": [
      "quarter_end_date"
    ],
    "Same_Store_Net_Operating_Income": [],
    "Rentable_SF": [
      "rentable_sf"
    ],
    "Leased_Percent": [
      "leased_percentage",
      "sf_leased",
      "sf_new_leased"
    ],
    "Revenue": [
      "base_rent",
      "cash_rental_income",
      "effective_rent_after_capex",
      "effective_rent_after_capex_opex",
      "rent_concessions",
      "rentable_sf",
      "rental_rate_cash_percent",
      "total_rents",
      "total_revenue"
    ],
    "Operating_Expenses": [
      "effective_rent_after_capex_opex",
      "expense_stop",
      "prop_operating_expense"
    ],
    "CapEx": [],
    "Implied_Cap_Rate": []
  },
  "geographic": {
    "Market": [],
    "Annualized_Rent": [],
    "Square_Feet": [],
    "Occupancy_Percent": [
      "leased_percent"
    ]
  }
}

def resolve(df: pd.DataFrame, canonical: str, domain: str = "quarterly") -> str:
    """
    Return the first column name in df that matches the canonical name or any of its aliases.
    domain: "quarterly" or "geographic"
    """
    domain_map: Dict[str, list] = ALIAS_MAP.get(domain, {})
    # prefer exact canonical if present
    if canonical in df.columns:
        return canonical
    for cand in [canonical] + domain_map.get(canonical, []):
        if cand in df.columns:
            return cand
        # try case-insensitive match
        for col in df.columns:
            if col.lower() == cand.lower():
                return col
    raise KeyError(f"Required column not found: {{canonical}} in domain '{{domain}}'. Known columns: {{list(df.columns)}}")
