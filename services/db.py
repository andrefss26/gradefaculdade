import os
import pandas as pd
from config import CSVS, HEADERS, DATA_DIR


def init_csvs():
    os.makedirs(DATA_DIR, exist_ok=True)
    for key, path in CSVS.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)


def read(key):
    try:
        df = pd.read_csv(CSVS[key], dtype=str).fillna("")
    except Exception:
        df = pd.DataFrame(columns=HEADERS[key])
    for col in HEADERS[key]:
        if col not in df.columns:
            df[col] = ""
    ordered = HEADERS[key] + [c for c in df.columns if c not in HEADERS[key]]
    return df[ordered].fillna("").astype(str)


def write(key, df):
    df.to_csv(CSVS[key], index=False)


def next_id(key, col="id"):
    df = read(key)
    if df.empty or col not in df.columns:
        return 1
    vals = pd.to_numeric(df[col], errors="coerce").dropna()
    return int(vals.max()) + 1 if not vals.empty else 1
