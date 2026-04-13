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


def _sort_horarios(hors: pd.DataFrame) -> pd.DataFrame:
    ordem = {"Segunda": 1, "Terca": 2, "Quarta": 3, "Quinta": 4, "Sexta": 5, "Sabado": 6, "Domingo": 7}
    return hors.assign(
        dia_ord=[ordem.get(d, 99) for d in hors["dia_semana"]],
        inicio_ord=[int(t.replace(":", "")) if isinstance(t, str) else 0 for t in hors["horario_inicio"]],
    ).sort_values(["dia_ord", "inicio_ord"]).reset_index(drop=True)


def _get_horario_sequence(hors: pd.DataFrame, start_id: str, blocos: int) -> list[str]:
    if blocos <= 1:
        return [str(start_id)]
    hors_sorted = _sort_horarios(hors)
    start_idx = hors_sorted[hors_sorted["id"] == str(start_id)].index
    if start_idx.empty:
        return []
    start_pos = start_idx[0]
    dia = hors_sorted.at[start_pos, "dia_semana"]
    sequence = []
    for offset in range(blocos):
        pos = start_pos + offset
        if pos >= len(hors_sorted):
            return []
        row = hors_sorted.iloc[pos]
        if str(row["dia_semana"]) != str(dia):
            return []
        sequence.append(str(row["id"]))
    return sequence


def _get_disciplina_duracao(disc_id: str, discs: pd.DataFrame) -> int:
    disc = discs[discs["id"] == str(disc_id)]
    if disc.empty:
        return 1
    try:
        return int(disc.iloc[0].get("duracao_blocos", 1) or 1)
    except Exception:
        return 1


def _montar_item_grade(row, profs, turmas, salas, discs, hors) -> dict | None:
    """Monta um dicionário completo de uma aula para exibição na grade."""
    duracao = _get_disciplina_duracao(row["id_disciplina"], discs)
    slots = _get_horario_sequence(hors, row["id_horario"], duracao)
    if not slots:
        return None
    first = hors[hors["id"] == slots[0]]
    last = hors[hors["id"] == slots[-1]]
    if first.empty or last.empty:
        return None
    first = first.iloc[0]
    last = last.iloc[0]
    return {
        "id_aula":       row["id_aula"],
        "professor":     _lookup(profs,  "id", row["id_professor"],  "nome"),
        "turma":         _lookup(turmas, "id", row["id_turma"],      "nome"),
        "sala":          _lookup(salas,  "id", row["id_sala"],       "nome"),
        "disciplina":    _lookup(discs,  "id", row["id_disciplina"], "nome"),
        "dia":           first["dia_semana"],
        "inicio":        first["horario_inicio"],
        "fim":           last["horario_fim"],
        "turno":         first["turno"],
        "id_professor":  row["id_professor"],
        "id_turma":      row["id_turma"],
        "id_sala":       row["id_sala"],
        "id_horario":    row["id_horario"],
        "id_disciplina": row["id_disciplina"],
    }


# ── Conflitos ─────────────────────────────────────────────────────────────────

def _obter_sequence_por_aula(aula_row, horarios, disciplinas) -> set[str]:
    duracao = _get_disciplina_duracao(aula_row.get("id_disciplina", ""), disciplinas)
    sequence = _get_horario_sequence(horarios, aula_row.get("id_horario", ""), duracao)
    return set(sequence)


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

    horarios = read("horarios")
    disciplinas = read("disciplinas")
    novaseq = set(_get_horario_sequence(horarios, str(dados.get("id_horario", "")), _get_disciplina_duracao(dados.get("id_disciplina", ""), disciplinas)))

    conflitos = set()
    for _, row in aulas.iterrows():
        existseq = _obter_sequence_por_aula(row, horarios, disciplinas)
        if not novaseq or not existseq or not novaseq.intersection(existseq):
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


def limpar_grade() -> bool:
    """Limpa todas as aulas da grade horária."""
    df = pd.DataFrame(columns=["id_aula", "id_professor", "id_turma", "id_sala", "id_horario", "id_disciplina"])
    write("aulas", df)
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
        sequence = _get_horario_sequence(
            hors,
            str(row["id_horario"]),
            _get_disciplina_duracao(row.get("id_disciplina", ""), discs),
        )
        if not sequence:
            continue

        first = hors[hors["id"] == sequence[0]]
        last = hors[hors["id"] == sequence[-1]]
        if first.empty or last.empty:
            continue
        first = first.iloc[0]
        last = last.iloc[0]

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
            "Dia da Semana":  first["dia_semana"],
            "Horario Inicio": first["horario_inicio"],
            "Horario Fim":    last["horario_fim"],
            "Turno":          first["turno"],
        })

    if filtro_valor:
        campo = "Turma" if tipo == "turma" else "Professor"
        rows = [r for r in rows if r[campo] == filtro_valor]

    return rows


# ── Alocação Automática ──────────────────────────────────────────────────────

def alocar_aulas_automaticamente(id_disciplina: str) -> tuple[bool, str, list[dict]]:
    """
    Aloca automaticamente aulas para todas as turmas baseado na carga horária da disciplina.
    Considera dias disponíveis do professor e horários disponíveis.
    Retorna (sucesso, mensagem, aulas_criadas).
    """
    discs = read("disciplinas")
    disc_row = discs[discs["id"] == str(id_disciplina)]
    if disc_row.empty:
        return False, "Disciplina não encontrada.", []
    
    disc = disc_row.iloc[0]
    id_prof = str(disc["id_professor"])
    carga_horaria = int(disc.get("carga_horaria", 0))
    duracao_blocos = _get_disciplina_duracao(id_disciplina, discs)
    
    if carga_horaria <= 0:
        return False, "Carga horária deve ser maior que 0.", []
    if carga_horaria % duracao_blocos != 0:
        return False, "Carga horária deve ser múltipla de duração em blocos.", []
    aulas_por_turma = carga_horaria // duracao_blocos
    
    # Obter dados do professor
    profs = read("professores")
    prof_row = profs[profs["id"] == id_prof]
    if prof_row.empty:
        return False, "Professor não encontrado.", []
    
    prof = prof_row.iloc[0]
    dias_disponiveis = str(prof.get("dias_disponiveis", "")).split(",")
    dias_disponiveis = [d.strip() for d in dias_disponiveis if d.strip()]
    
    # Obter turmas, salas e horários
    turmas = read("turmas")
    salas = read("salas")
    horarios = read("horarios")
    aulas = read("aulas")
    
    if salas.empty:
        return False, "Nenhuma sala disponível.", []
    
    sala_padrao = salas.iloc[0]["id"]  # Pega primeira sala
    
    aulas_criadas = []
    
    # Para cada turma, criar as aulas necessárias
    for _, turma in turmas.iterrows():
        id_turma = str(turma["id"])
        
        # Encontrar horários disponíveis para essa turma/professor/sala
        slots_disponiveis = []
        
        for _, horario in horarios.iterrows():
            dia = str(horario["dia_semana"]).strip()
            id_horario = str(horario["id"])
            
            # Filtrar por dias disponíveis do professor
            if dia not in dias_disponiveis:
                continue
            
            sequence = _get_horario_sequence(horarios, id_horario, duracao_blocos)
            if not sequence:
                continue

            conflito_existente = False
            for _, aula in aulas.iterrows():
                seq_aula = _obter_sequence_por_aula(aula, horarios, discs)
                if not seq_aula.intersection(sequence):
                    continue
                if aula["id_professor"] == id_prof or aula["id_turma"] == id_turma or aula["id_sala"] == sala_padrao:
                    conflito_existente = True
                    break
            if conflito_existente:
                continue
            
            slots_disponiveis.append(horario)
        
        # Alocar aulas necessárias para completar a carga horária
        for i in range(aulas_por_turma):
            if i >= len(slots_disponiveis):
                break
            
            horario_slot = slots_disponiveis[i]
            sequence = _get_horario_sequence(horarios, str(horario_slot["id"]), duracao_blocos)
            if not sequence:
                continue
            
            primeiro = horarios[horarios["id"] == sequence[0]].iloc[0]
            ultimo = horarios[horarios["id"] == sequence[-1]].iloc[0]
            
            # Criar aula
            aula_dados = {
                "id_professor": id_prof,
                "id_turma": id_turma,
                "id_sala": sala_padrao,
                "id_disciplina": str(id_disciplina),
                "id_horario": str(horario_slot["id"]),
            }
            
            ok, conflitos, id_aula = criar_aula(aula_dados)
            if ok:
                aulas_criadas.append({
                    "id_aula": id_aula,
                    "turma": turma["nome"],
                    "dia": primeiro["dia_semana"],
                    "horario": f"{primeiro['horario_inicio']}–{ultimo['horario_fim']}",
                })
    
    if not aulas_criadas:
        return False, "Não foi possível alocar nenhuma aula. Verifique disponibilidade.", []
    
    return True, f"Alojadas {len(aulas_criadas)} aula(s).", aulas_criadas
