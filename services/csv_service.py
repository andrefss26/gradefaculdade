import os
import pandas as pd
from config import DATA_DIR, CSVS

def _path(nome): return os.path.join(DATA_DIR, f"{nome}.csv")

def init_csvs():
    os.makedirs(DATA_DIR, exist_ok=True)
    for nome, cols in CSVS.items():
        p = _path(nome)
        if not os.path.exists(p):
            pd.DataFrame(columns=cols).to_csv(p, index=False)

def read(nome: str) -> pd.DataFrame:
    p = _path(nome)
    if not os.path.exists(p):
        return pd.DataFrame(columns=CSVS.get(nome, []))
    try:
        df = pd.read_csv(p, dtype=str).fillna("")
        return df
    except Exception:
        return pd.DataFrame(columns=CSVS.get(nome, []))

def write(nome: str, df: pd.DataFrame):
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(_path(nome), index=False)

def next_id(nome: str, col_id: str) -> int:
    df = read(nome)
    if df.empty or col_id not in df.columns:
        return 1
    try:
        return int(pd.to_numeric(df[col_id], errors="coerce").max()) + 1
    except Exception:
        return 1
