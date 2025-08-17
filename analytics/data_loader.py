from functools import lru_cache
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@lru_cache(maxsize=1)
def load():
    q = pd.read_csv(DATA_DIR / "Piedmont_Quarterly_Data.csv")
    g = pd.read_csv(DATA_DIR / "Piedmont_Geographic_Data.csv")
    return q, g

def latest_quarter(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["fiscal_year", "fiscal_quarter"]).tail(1)
