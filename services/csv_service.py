"""
Serviço responsável por toda a leitura e escrita nos arquivos CSV.
Todas as outras camadas usam este módulo para acessar os dados.
"""
import os
import pandas as pd
from config import CSVS, HEADERS, DATA_DIR


def init_csvs():
    """Cria os arquivos CSV caso não existam ainda."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for key, path in CSVS.items():
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write(",".join(HEADERS[key]) + "\n")


def read(key: str) -> pd.DataFrame:
    """Lê um CSV e retorna um DataFrame com valores vazios normalizados."""
    try:
        df = pd.read_csv(CSVS[key], dtype=str)
        for col in HEADERS[key]:
            if col not in df.columns:
                df[col] = ""
        df = df.reindex(columns=HEADERS[key])
        return df.fillna("")
    except Exception:
        return pd.DataFrame(columns=HEADERS[key])


def write(key: str, df: pd.DataFrame):
    """Grava um DataFrame no CSV correspondente."""
    df.to_csv(CSVS[key], index=False)


def next_id(key: str, id_col: str = "id") -> int:
    """Retorna o próximo ID disponível para uma entidade."""
    df = read(key)
    if df.empty or id_col not in df.columns:
        return 1
    ids = pd.to_numeric(df[id_col], errors="coerce").dropna()
    return int(ids.max()) + 1 if not ids.empty else 1
