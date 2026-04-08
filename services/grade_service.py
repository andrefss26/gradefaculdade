"""
Serviço da grade horária.
Responsável por: alocar aulas, detectar conflitos,
montar a grade visual e gerar os dados de exportação.
"""
import pandas as pd
from services.csv_service import read, write, next_id


# ── Helpers internos ───────────────────────────────────────────────────────────

def _lookup(df: pd.DataFrame, id_col: str, id_val: str, campo: str) -> str:
    """Busca um campo em um DataFrame pelo valor de uma coluna de ID."""
    row = df[df[id_col] == str(id_val)]
    return row.iloc[0][campo] if not row.empty else id_val


def _montar_item_grade(row, profs, turmas, salas, discs, hors) -> dict | None:
    """Monta um dicionário completo de uma aula para exibição na grade."""
    h = hors[hors["id"] == str(row["id_horario"])]
    if h.empty:
        return None
    h = h.iloc[0]
    return {
        "id_aula":       row["id_aula"],
        "professor":     _lookup(profs,  "id", row["id_professor"],  "nome"),
        "turma":         _lookup(turmas, "id", row["id_turma"],      "nome"),
        "sala":          _lookup(salas,  "id", row["id_sala"],       "nome"),
        "disciplina":    _lookup(discs,  "id", row["id_disciplina"], "nome"),
        "dia":           h["dia_semana"],
        "inicio":        h["horario_inicio"],
        "fim":           h["horario_fim"],
        "turno":         h["turno"],
        "id_professor":  row["id_professor"],
        "id_turma":      row["id_turma"],
        "id_sala":       row["id_sala"],
        "id_horario":    row["id_horario"],
        "id_disciplina": row["id_disciplina"],
    }


# ── Conflitos ─────────────────────────────────────────────────────────────────

def verificar_conflitos(dados: dict, excluir_id: str = "") -> list[str]:
    """
    Verifica conflitos de horário conforme as regras de negócio:
      RN-01 — Professor não pode ter dois horários simultâneos.
      RN-02 — Sala não pode ser usada por duas turmas ao mesmo tempo.
              Turma não pode ter duas aulas no mesmo horário.

    Retorna lista de mensagens de conflito (vazia = sem conflitos).
    """
    aulas = read("aulas")
    if not aulas.empty and excluir_id:
        aulas = aulas[aulas["id_aula"] != str(excluir_id)]

    conflitos = set()
    for _, row in aulas.iterrows():
        if row["id_horario"] != str(dados.get("id_horario", "")):
            continue
        if row["id_professor"] == str(dados.get("id_professor", "")):
            conflitos.add("Professor já possui aula neste horário.")
        if row["id_turma"] == str(dados.get("id_turma", "")):
            conflitos.add("Turma já possui aula neste horário.")
        if row["id_sala"] == str(dados.get("id_sala", "")):
            conflitos.add("Sala já está ocupada neste horário.")

    return list(conflitos)


# ── CRUD de Aulas ─────────────────────────────────────────────────────────────

def criar_aula(dados: dict) -> tuple[bool, list[str], str]:
    """
    Tenta criar uma nova aula após verificar conflitos.
    Retorna (sucesso, lista_de_conflitos, id_gerado).
    """
    conflitos = verificar_conflitos(dados)
    if conflitos:
        return False, conflitos, ""

    aulas = read("aulas")
    dados["id_aula"] = str(next_id("aulas", "id_aula"))
    novo = pd.DataFrame([dados])
    aulas = pd.concat([aulas, novo], ignore_index=True)
    write("aulas", aulas)
    return True, [], dados["id_aula"]


def editar_aula(id_aula: str, dados: dict) -> tuple[bool, list[str]]:
    """
    Atualiza uma aula existente após verificar conflitos.
    Retorna (sucesso, lista_de_conflitos).
    """
    conflitos = verificar_conflitos(dados, excluir_id=id_aula)
    if conflitos:
        return False, conflitos

    aulas = read("aulas")
    idx = aulas[aulas["id_aula"] == str(id_aula)].index
    if idx.empty:
        return False, ["Aula não encontrada."]

    for campo, valor in dados.items():
        if campo in aulas.columns:
            aulas.at[idx[0], campo] = str(valor)
    write("aulas", aulas)
    return True, []


def deletar_aula(id_aula: str) -> bool:
    """Remove uma aula pelo ID. Retorna True se removida."""
    aulas = read("aulas")
    novo_df = aulas[aulas["id_aula"] != str(id_aula)]
    write("aulas", novo_df)
    return True


# ── Leitura da Grade ──────────────────────────────────────────────────────────

def obter_grade() -> list[dict]:
    """
    Retorna todas as aulas com os dados completos (nomes resolvidos),
    prontas para exibição na grade visual.
    """
    aulas = read("aulas")
    if aulas.empty:
        return []

    profs  = read("professores")
    turmas = read("turmas")
    salas  = read("salas")
    discs  = read("disciplinas")
    hors   = read("horarios")

    resultado = []
    for _, row in aulas.iterrows():
        item = _montar_item_grade(row, profs, turmas, salas, discs, hors)
        if item:
            resultado.append(item)
    return resultado


# ── Resumo do sistema ─────────────────────────────────────────────────────────

def obter_resumo() -> dict:
    """
    Retorna os totais de cada entidade para exibição no Dashboard.
    """
    turmas = read("turmas")
    total_alunos = 0
    if not turmas.empty and "quantidade_alunos" in turmas.columns:
        total_alunos = pd.to_numeric(
            turmas["quantidade_alunos"], errors="coerce"
        ).fillna(0).sum()

    return {
        "professores": len(read("professores")),
        "turmas":      len(turmas),
        "disciplinas": len(read("disciplinas")),
        "salas":       len(read("salas")),
        "aulas":       len(read("aulas")),
        "alunos":      int(total_alunos),
    }


# ── Exportação CSV ────────────────────────────────────────────────────────────

def exportar_grade(tipo: str, filtro_valor: str = "") -> list[dict]:
    """
    Monta a lista de linhas para exportação CSV da grade.
    tipo: 'turma' ou 'professor'
    filtro_valor: nome do filtro a aplicar (opcional).
    """
    aulas  = read("aulas")
    profs  = read("professores")
    turmas = read("turmas")
    salas  = read("salas")
    hors   = read("horarios")
    discs  = read("disciplinas")

    rows = []
    for _, row in aulas.iterrows():
        h = hors[hors["id"] == str(row["id_horario"])]
        if h.empty:
            continue
        h = h.iloc[0]

        prof_row  = profs[profs["id"]   == str(row["id_professor"])]
        turma_row = turmas[turmas["id"] == str(row["id_turma"])]
        sala_row  = salas[salas["id"]   == str(row["id_sala"])]
        disc_row  = discs[discs["id"]   == str(row["id_disciplina"])]

        rows.append({
            "Turma":          turma_row.iloc[0]["nome"]  if not turma_row.empty else "",
            "Professor":      prof_row.iloc[0]["nome"]   if not prof_row.empty  else "",
            "Disciplina":     disc_row.iloc[0]["nome"]   if not disc_row.empty  else "",
            "Sala":           sala_row.iloc[0]["nome"]   if not sala_row.empty  else "",
            "Tipo Sala":      sala_row.iloc[0]["tipo"]   if not sala_row.empty  else "",
            "Dia da Semana":  h["dia_semana"],
            "Horario Inicio": h["horario_inicio"],
            "Horario Fim":    h["horario_fim"],
            "Turno":          h["turno"],
        })

    if filtro_valor:
        campo = "Turma" if tipo == "turma" else "Professor"
        rows = [r for r in rows if r[campo] == filtro_valor]

    return rows
