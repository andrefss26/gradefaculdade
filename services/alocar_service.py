"""
Serviço de Alocação Automática — versão vetorizada (sem iterrows no loop interno).

O problema da versão anterior era _slot_livre e _primeira_sala_livre
usando iterrows() sobre o cache a cada slot candidato, causando O(n³)
e travamento com 16 turmas × 20 disciplinas × 50 horários.

Solução: pré-computar sets de ocupação em dicionários indexados por id_horario.
"""
from __future__ import annotations
import pandas as pd
from services.csv_service import read, write
from services.auth_service import verificar_permissao
from services.grade_service import _sort_horarios, _get_horario_sequence, _get_disciplina_duracao, _lookup
from config import MAPA_CURSO_DISCS


def _build_mapa(discs: pd.DataFrame) -> dict[str, list[str]]:
    if "id_curso" not in discs.columns:
        return MAPA_CURSO_DISCS
    mapa: dict[str, list[str]] = {}
    for _, r in discs.iterrows():
        mapa.setdefault(str(r["id_curso"]).strip(), []).append(str(r["id"]).strip())
    return mapa if mapa else MAPA_CURSO_DISCS


def _build_ocupacao(cache: pd.DataFrame, horarios: pd.DataFrame, discs: pd.DataFrame):
    """
    Retorna três dicts indexados por id_horario:
      prof_slots[id_hor]  = set de id_professor ocupados naquele slot
      turma_slots[id_hor] = set de id_turma ocupados naquele slot
      sala_slots[id_hor]  = set de id_sala ocupados naquele slot

    Para disciplinas com duracao_blocos > 1, todos os blocos da sequência
    são marcados.
    """
    prof_slots:  dict[str, set] = {}
    turma_slots: dict[str, set] = {}
    sala_slots:  dict[str, set] = {}

    if cache.empty:
        return prof_slots, turma_slots, sala_slots

    for _, a in cache.iterrows():
        dur = _get_disciplina_duracao(str(a.get("id_disciplina", "")), discs)
        seq = _get_horario_sequence(horarios, str(a.get("id_horario", "")), dur)
        for hid in seq:
            prof_slots.setdefault(hid, set()).add(str(a["id_professor"]))
            turma_slots.setdefault(hid, set()).add(str(a["id_turma"]))
            sala_slots.setdefault(hid, set()).add(str(a["id_sala"]))

    return prof_slots, turma_slots, sala_slots


def alocar_grade_completa(
    usuario: dict,
    mapa_curso_discs: dict[str, list[str]] | None = None,
) -> tuple[bool, str, list[dict]]:
    """
    Aloca automaticamente aulas para TODAS as turmas e disciplinas.

    Usa dicionários de ocupação pré-computados para verificar conflitos
    em O(1) por slot, sem iterrows no loop interno.
    """
    verificar_permissao(usuario, "aulas", "criar")

    # ── Carregar dados ────────────────────────────────────────────────────────
    discs    = read("disciplinas")
    turmas   = read("turmas")
    salas    = read("salas")
    horarios = read("horarios")
    profs    = read("professores")

    for nome, df in [("disciplinas", discs), ("turmas", turmas),
                     ("salas", salas), ("horarios", horarios)]:
        if df.empty:
            return False, f"Nenhum(a) {nome} cadastrado(a).", []

    # Disponibilidade e limite diário dos professores
    prof_dias: dict[str, set[str]] = {}
    prof_max:  dict[str, int] = {}
    for _, p in profs.iterrows():
        pid = str(p["id"])
        prof_dias[pid] = {d.strip() for d in str(p.get("dias_disponiveis", "")).split(",") if d.strip()}
        try:
            prof_max[pid] = int(p.get("max_aulas_dia", 6) or 6)
        except (ValueError, TypeError):
            prof_max[pid] = 6

    hors_ord = _sort_horarios(horarios)
    mapa     = mapa_curso_discs or _build_mapa(discs)

    # Dia de cada id_horario (lookup rápido)
    hor_dia: dict[str, str] = {str(r["id"]): str(r["dia_semana"]) for _, r in horarios.iterrows()}

    # Lista de salas ordenada por capacidade desc (maior primeiro = menos chance de conflito)
    salas_ord = salas.copy()
    if "capacidade" in salas_ord.columns:
        salas_ord["_cap"] = pd.to_numeric(salas_ord["capacidade"], errors="coerce").fillna(0)
        salas_ord = salas_ord.sort_values("_cap", ascending=False).reset_index(drop=True)

    # Cache + estrutura de ocupação
    cache = read("aulas").copy()
    if cache.empty:
        cache = pd.DataFrame(columns=["id_aula", "id_professor", "id_turma",
                                       "id_sala", "id_disciplina", "id_horario"])

    prof_slots, turma_slots, sala_slots = _build_ocupacao(cache, horarios, discs)

    # Próximo ID — calculado uma vez
    try:
        proximo_id = int(pd.to_numeric(cache["id_aula"], errors="coerce").max()) + 1
        if pd.isna(proximo_id):
            proximo_id = 1
    except Exception:
        proximo_id = 1

    # Contagem de aulas por (professor, dia) já existentes
    aulas_dia: dict[str, int] = {}
    for hid, profs_set in prof_slots.items():
        dia = hor_dia.get(hid, "")
        for pid in profs_set:
            aulas_dia[f"{pid}:{dia}"] = aulas_dia.get(f"{pid}:{dia}", 0) + 1

    novas_aulas: list[dict] = []
    criadas:     list[dict] = []
    avisos:      list[str]  = []

    # ── Loop principal ────────────────────────────────────────────────────────
    for _, turma in turmas.iterrows():
        id_turma   = str(turma["id"])
        curso_id   = str(turma.get("id_curso", "")).strip()
        try:
            num_alunos = int(turma.get("quantidade_alunos", 0) or 0)
        except (ValueError, TypeError):
            num_alunos = 0

        discs_curso = mapa.get(curso_id, [])
        if not discs_curso:
            avisos.append(f"Turma '{turma['nome']}': sem disciplinas mapeadas (curso {curso_id}).")
            continue

        for disc_id in discs_curso:
            dr = discs[discs["id"] == str(disc_id)]
            if dr.empty:
                continue

            disc    = dr.iloc[0]
            id_prof = str(disc["id_professor"])
            dur     = _get_disciplina_duracao(disc_id, discs)
            try:
                carga = int(disc.get("carga_horaria", 0) or 0)
            except (ValueError, TypeError):
                carga = 0

            if carga <= 0 or (dur > 0 and carga % dur != 0):
                avisos.append(f"Disc '{disc['nome']}': carga inválida ({carga}h/{dur} blocos).")
                continue

            necessarias = carga // dur if dur > 0 else 0
            dias_prof   = prof_dias.get(id_prof, set())
            alocadas    = 0

            for _, hor in hors_ord.iterrows():
                if alocadas >= necessarias:
                    break

                dia        = str(hor["dia_semana"]).strip()
                id_horario = str(hor["id"])

                # ① Dia disponível?
                if dia not in dias_prof:
                    continue

                # ② Limite diário do professor
                if aulas_dia.get(f"{id_prof}:{dia}", 0) >= prof_max.get(id_prof, 6):
                    continue

                # ③ Calcular sequência de blocos
                seq = _get_horario_sequence(horarios, id_horario, dur)
                if not seq:
                    continue

                # ④ Conflito de professor ou turma em qualquer bloco da sequência?
                conflito = False
                for hid in seq:
                    if id_prof  in prof_slots.get(hid, set()):
                        conflito = True; break
                    if id_turma in turma_slots.get(hid, set()):
                        conflito = True; break
                if conflito:
                    continue

                # ⑤ Encontrar sala livre com capacidade suficiente
                id_sala = None
                for _, s in salas_ord.iterrows():
                    cap = 0
                    if "capacidade" in s.index:
                        try:
                            cap = int(s["capacidade"])
                        except (ValueError, TypeError):
                            cap = 9999
                    else:
                        cap = 9999
                    if cap < num_alunos:
                        continue
                    sid = str(s["id"])
                    sala_livre = all(sid not in sala_slots.get(hid, set()) for hid in seq)
                    if sala_livre:
                        id_sala = sid
                        break

                if id_sala is None:
                    continue

                # ── Registrar aula ────────────────────────────────────────────
                novo_id = str(proximo_id)
                proximo_id += 1

                aula = {
                    "id_aula":       novo_id,
                    "id_professor":  id_prof,
                    "id_turma":      id_turma,
                    "id_sala":       id_sala,
                    "id_disciplina": str(disc_id),
                    "id_horario":    id_horario,
                }
                novas_aulas.append(aula)

                # Atualizar índices de ocupação
                for hid in seq:
                    prof_slots.setdefault(hid, set()).add(id_prof)
                    turma_slots.setdefault(hid, set()).add(id_turma)
                    sala_slots.setdefault(hid, set()).add(id_sala)

                aulas_dia[f"{id_prof}:{dia}"] = aulas_dia.get(f"{id_prof}:{dia}", 0) + 1
                alocadas += 1

                pri = horarios[horarios["id"] == seq[0]].iloc[0]
                ult = horarios[horarios["id"] == seq[-1]].iloc[0]
                criadas.append({
                    "id_aula":    novo_id,
                    "turma":      turma["nome"],
                    "disciplina": disc["nome"],
                    "professor":  _lookup(profs, "id", id_prof, "nome"),
                    "sala":       _lookup(salas,  "id", id_sala,  "nome"),
                    "dia":        pri["dia_semana"],
                    "horario":    f"{pri['horario_inicio']}–{ult['horario_fim']}",
                })

            if alocadas < necessarias:
                avisos.append(
                    f"Turma '{turma['nome']}' / '{disc['nome']}': "
                    f"{alocadas}/{necessarias} aulas. Verifique disponibilidade."
                )

    # ── Gravar tudo no CSV em uma única operação ──────────────────────────────
    if novas_aulas:
        existentes = read("aulas")
        df_final = pd.concat([existentes, pd.DataFrame(novas_aulas)], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["id_aula"], keep="first")
        write("aulas", df_final)

    if not criadas:
        motivo = " | ".join(avisos[:3]) if avisos else "Verifique disponibilidade, horários e salas."
        return False, f"Nenhuma aula pôde ser alocada. {motivo}", []

    t_at = len({a["turma"]      for a in criadas})
    d_at = len({a["disciplina"] for a in criadas})
    msg  = f"{len(criadas)} aula(s) alocada(s) | {t_at} turma(s) | {d_at} disciplina(s)."
    if avisos:
        msg += f" ⚠️ {len(avisos)} aviso(s): " + " | ".join(avisos)

    return True, msg, criadas


def relatorio_alocacao(mapa_curso_discs: dict | None = None) -> dict:
    discs  = read("disciplinas")
    turmas = read("turmas")
    aulas  = read("aulas")
    mapa   = mapa_curso_discs or _build_mapa(discs)
    completas, parciais, zeradas, avisos = [], [], [], []
    for _, turma in turmas.iterrows():
        id_t  = str(turma["id"])
        curso = str(turma.get("id_curso", "")).strip()
        at    = aulas[aulas["id_turma"] == id_t] if not aulas.empty else pd.DataFrame()
        esp   = 0
        for disc_id in mapa.get(curso, []):
            dr = discs[discs["id"] == str(disc_id)]
            if dr.empty: continue
            d = dr.iloc[0]
            try:
                dur = max(_get_disciplina_duracao(disc_id, discs), 1)
                esp += int(d.get("carga_horaria", 0) or 0) // dur
            except (ValueError, TypeError):
                pass
        al = len(at)
        if   al == 0:  zeradas.append(turma["nome"])
        elif al < esp: parciais.append({"turma": turma["nome"], "alocadas": al, "esperadas": esp})
        else:          completas.append(turma["nome"])
        if al < esp:   avisos.append(f"Turma '{turma['nome']}': {al}/{esp} aulas.")
    return {
        "total_aulas":      len(aulas) if not aulas.empty else 0,
        "turmas_completas": completas,
        "turmas_parciais":  parciais,
        "turmas_zeradas":   zeradas,
        "avisos":           avisos,
    }
