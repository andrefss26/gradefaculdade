import pandas as pd
from services.db import read, write, next_id

VALID = {"professores","disciplinas","turmas","salas","horarios"}
REQ = {
    "professores": ["nome","email","disciplinas_ids"],
    "disciplinas": ["nome","curso","carga_horaria"],
    "turmas": ["nome","curso","periodo","semestre","disciplinas_exigidas"],
    "salas": ["nome"],
    "horarios": ["turno","dia_semana","horario_inicio","horario_fim"],
}


def _s(v):
    return str(v).strip()


def _split_ids(v):
    return [x for x in [_s(i) for i in str(v or "").split(",")] if x]


def _validar(ent, dados, id_val=""):
    if ent not in VALID:
        raise ValueError("Entidade inválida")
    for campo in REQ.get(ent, []):
        if not _s(dados.get(campo, "")):
            raise ValueError(f"Campo obrigatório: {campo}")
    if ent == "professores":
        if not _split_ids(dados.get("disciplinas_ids", "")):
            raise ValueError("Professor deve informar ao menos uma matéria")
        email = _s(dados.get("email", ""))
        if email:
            df = read("professores")
            dup = df[(df["email"] == email) & (df["id"] != _s(id_val))]
            if not dup.empty:
                raise ValueError("E-mail já cadastrado")
    if ent == "turmas":
        if not _split_ids(dados.get("disciplinas_exigidas", "")):
            raise ValueError("Turma deve informar ao menos uma matéria exigida")
        try:
            sem = int(_s(dados.get("semestre", "0")))
            if sem <= 0:
                raise ValueError
        except Exception:
            raise ValueError("Semestre inválido")


def listar(ent):
    return read(ent).to_dict("records") if ent in VALID else []


def criar(ent, dados):
    _validar(ent, dados)
    df = read(ent)
    novo = {c: _s(dados.get(c, "")) for c in df.columns}
    novo["id"] = str(next_id(ent))
    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    write(ent, df)
    return novo


def atualizar(ent, id_val, dados):
    if ent not in VALID:
        return False
    df = read(ent)
    idx = df[df["id"] == str(id_val)].index
    if idx.empty:
        return False
    dados_full = {c: df.at[idx[0], c] for c in df.columns}
    for k, v in dados.items():
        if k in df.columns:
            dados_full[k] = _s(v)
    _validar(ent, dados_full, id_val=id_val)
    for c in df.columns:
        if c != "id":
            df.at[idx[0], c] = _s(dados_full.get(c, ""))
    write(ent, df)
    return True


def deletar(ent, id_val):
    if ent not in VALID:
        return False
    df = read(ent)
    write(ent, df[df["id"] != str(id_val)])
    return True
