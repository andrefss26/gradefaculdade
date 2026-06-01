from collections import defaultdict

import pandas as pd

from services.db import next_id, read, write


DIAS_ORD = {"Segunda": 0, "Terca": 1, "Quarta": 2, "Quinta": 3, "Sexta": 4}
AULAS_COLS = ["id_aula", "id_professor", "id_turma", "id_sala", "id_horario", "id_disciplina"]


def _s(v):
    return str(v).strip()


def _i(v, default=0):
    try:
        return int(float(_s(v)))
    except Exception:
        return default


def _split_ids(v):
    out = []
    for raw in _s(v).split(","):
        val = raw.strip()
        if val and val not in out:
            out.append(val)
    return out


def _map_by_id(df):
    out = {}
    for _, row in df.iterrows():
        rid = _s(row.get("id", ""))
        if rid:
            out[rid] = {k: _s(v) for k, v in row.items()}
    return out


def _ord_horarios(horarios_df, turno=""):
    df = horarios_df.copy()
    if turno:
        df = df[df["turno"] == _s(turno)]
    if df.empty:
        return []
    df["__dia"] = df["dia_semana"].map(lambda d: DIAS_ORD.get(_s(d), 99))
    df["__ini"] = df["horario_inicio"].fillna("")
    df = df.sort_values(["__dia", "__ini", "id"])
    return df.to_dict("records")


def _disciplinas_por_turma(turma, disciplinas_df):
    ids = _split_ids(turma.get("disciplinas_exigidas", ""))
    if ids:
        return ids
    curso = _s(turma.get("curso", ""))
    semestre = _s(turma.get("semestre", ""))
    if curso and semestre and "semestre" in disciplinas_df.columns:
        base = disciplinas_df[(disciplinas_df["curso"] == curso) & (disciplinas_df["semestre"] == semestre)]
        vals = [_s(v) for v in base["id"].tolist() if _s(v)]
        if vals:
            return vals
    if curso:
        base = disciplinas_df[disciplinas_df["curso"] == curso]
        vals = [_s(v) for v in base["id"].tolist() if _s(v)]
        if vals:
            return vals
    return []


def _disciplinas_por_professor(professores_df, disciplinas_df):
    padrao = defaultdict(list)
    if "id_professor" in disciplinas_df.columns:
        for _, disc in disciplinas_df.iterrows():
            pid = _s(disc.get("id_professor", ""))
            did = _s(disc.get("id", ""))
            if pid and did and did not in padrao[pid]:
                padrao[pid].append(did)
    out = {}
    for _, prof in professores_df.iterrows():
        pid = _s(prof.get("id", ""))
        manual = _split_ids(prof.get("disciplinas_ids", ""))
        merged = manual + [d for d in padrao.get(pid, []) if d not in manual]
        out[pid] = set(merged)
    return out


def _escolher_sala(salas, ocupadas, qtd_alunos):
    livres = [s for s in salas if _s(s.get("id", "")) not in ocupadas]
    if not livres:
        return ""
    com_capacidade = [s for s in livres if _i(s.get("capacidade", "0"), 0) >= qtd_alunos]
    alvo = com_capacidade if com_capacidade else livres
    alvo = sorted(alvo, key=lambda s: (_i(s.get("capacidade", "0"), 0), _s(s.get("id", ""))))
    return _s(alvo[0].get("id", ""))


def _escolher_sala_bloco(salas, ocup_sala, hids, qtd_alunos):
    livres = []
    for sala in salas:
        sid = _s(sala.get("id", ""))
        if sid and all(sid not in ocup_sala[hid] for hid in hids):
            livres.append(sala)
    if not livres:
        return ""
    com_capacidade = [s for s in livres if _i(s.get("capacidade", "0"), 0) >= qtd_alunos]
    alvo = com_capacidade if com_capacidade else livres
    alvo = sorted(alvo, key=lambda s: (_i(s.get("capacidade", "0"), 0), _s(s.get("id", ""))))
    return _s(alvo[0].get("id", ""))


def _janelas_2x2(horarios_turno):
    por_dia = defaultdict(list)
    for h in horarios_turno:
        dia = _s(h.get("dia_semana", ""))
        if dia:
            por_dia[dia].append(h)
    janelas = []
    for dia, hs in por_dia.items():
        hs = sorted(hs, key=lambda h: (_s(h.get("horario_inicio", "")), _s(h.get("id", ""))))
        for i in range(0, max(len(hs) - 3, 0)):
            janelas.append((dia, hs[i:i + 2], hs[i + 2:i + 4]))
    return sorted(janelas, key=lambda x: (DIAS_ORD.get(x[0], 99), _s(x[1][0].get("horario_inicio", ""))))


def _blocos_pendentes(exigidas, disc_map):
    pendentes = []
    for did in exigidas:
        carga = _i(disc_map.get(did, {}).get("carga_horaria", "1"), 1)
        if carga <= 0:
            carga = 1
        blocos = max(1, (carga + 1) // 2)
        pendentes.extend([did] * blocos)
    return pendentes


def _pares_pendentes(pendentes):
    pares = []
    for i, d1 in enumerate(pendentes):
        for j in range(i + 1, len(pendentes)):
            if d1 != pendentes[j]:
                pares.append((i, j))
    for i, d1 in enumerate(pendentes):
        for j in range(i + 1, len(pendentes)):
            if d1 == pendentes[j]:
                pares.append((i, j))
    return pares


def _escolher_prof_bloco(did, hids, dia, prof_info, ocup_prof, carga_dia_prof, carga_total_prof, extra=None):
    extra = extra or {}
    candidatos = []
    for pid, info in prof_info.items():
        if did not in info["disciplinas"]:
            continue
        if info["dias"] and dia not in info["dias"]:
            continue
        if any(pid in ocup_prof[hid] for hid in hids):
            continue
        if carga_dia_prof[(pid, dia)] + extra.get(pid, 0) + len(hids) > info["max_dia"]:
            continue
        candidatos.append(pid)
    candidatos = sorted(candidatos, key=lambda pid: (carga_dia_prof[(pid, dia)] + extra.get(pid, 0), carga_total_prof[pid], _s(pid)))
    return candidatos[0] if candidatos else ""


def _validar_aula(dados, excluir_id=""):
    conflitos = []
    campos = ["id_professor", "id_turma", "id_sala", "id_horario", "id_disciplina"]
    payload = {k: _s(dados.get(k, "")) for k in campos}
    for campo in campos:
        if not payload[campo]:
            conflitos.append(f"Campo obrigatório: {campo}")
    if conflitos:
        return conflitos

    professores = read("professores")
    turmas = read("turmas")
    salas = read("salas")
    horarios = read("horarios")
    disciplinas = read("disciplinas")

    if professores[professores["id"] == payload["id_professor"]].empty:
        conflitos.append("Professor não encontrado")
    if turmas[turmas["id"] == payload["id_turma"]].empty:
        conflitos.append("Turma não encontrada")
    if salas[salas["id"] == payload["id_sala"]].empty:
        conflitos.append("Sala não encontrada")
    if horarios[horarios["id"] == payload["id_horario"]].empty:
        conflitos.append("Horário não encontrado")
    if disciplinas[disciplinas["id"] == payload["id_disciplina"]].empty:
        conflitos.append("Disciplina não encontrada")
    if conflitos:
        return conflitos

    prof_row = professores[professores["id"] == payload["id_professor"]].iloc[0].to_dict()
    turma_row = turmas[turmas["id"] == payload["id_turma"]].iloc[0].to_dict()
    hor_row = horarios[horarios["id"] == payload["id_horario"]].iloc[0].to_dict()

    dia = _s(hor_row.get("dia_semana", ""))
    dias = set(_split_ids(prof_row.get("dias_disponiveis", "")))
    if dias and dia not in dias:
        conflitos.append("Professor indisponível neste dia")

    turno_turma = _s(turma_row.get("periodo", ""))
    turno_hor = _s(hor_row.get("turno", ""))
    if turno_turma and turno_hor and turno_turma != turno_hor:
        conflitos.append("Horário incompatível com período da turma")

    prof_disciplinas = _disciplinas_por_professor(professores, disciplinas)
    if payload["id_disciplina"] not in prof_disciplinas.get(payload["id_professor"], set()):
        conflitos.append("Professor não ministra esta disciplina")

    turma_disciplinas = _disciplinas_por_turma(turma_row, disciplinas)
    if turma_disciplinas and payload["id_disciplina"] not in turma_disciplinas:
        conflitos.append("Disciplina não está nas exigências da turma")

    conflitos.extend(check_conflitos(payload, excluir_id=excluir_id))
    out = []
    for c in conflitos:
        if c not in out:
            out.append(c)
    return out


def check_conflitos(dados=None, excluir_id=""):
    aulas = read("aulas")
    if excluir_id:
        aulas = aulas[aulas["id_aula"] != _s(excluir_id)]

    if isinstance(dados, dict):
        id_horario = _s(dados.get("id_horario", ""))
        if not id_horario:
            return []
        slot = aulas[aulas["id_horario"] == id_horario]
        conflitos = []
        id_professor = _s(dados.get("id_professor", ""))
        id_turma = _s(dados.get("id_turma", ""))
        id_sala = _s(dados.get("id_sala", ""))
        if id_professor and not slot[slot["id_professor"] == id_professor].empty:
            conflitos.append("Professor já possui aula neste horário")
        if id_turma and not slot[slot["id_turma"] == id_turma].empty:
            conflitos.append("Turma já possui aula neste horário")
        if id_sala and not slot[slot["id_sala"] == id_sala].empty:
            conflitos.append("Sala já está ocupada neste horário")
        return conflitos

    if aulas.empty:
        return []

    conflitos = set()
    for _, grp in aulas.groupby("id_horario"):
        p = grp[(grp["id_professor"] != "") & grp.duplicated("id_professor", keep=False)]
        t = grp[(grp["id_turma"] != "") & grp.duplicated("id_turma", keep=False)]
        s = grp[(grp["id_sala"] != "") & grp.duplicated("id_sala", keep=False)]
        if not p.empty:
            conflitos.add("Conflito de professor")
        if not t.empty:
            conflitos.add("Conflito de turma")
        if not s.empty:
            conflitos.add("Conflito de sala")
    return sorted(list(conflitos))


def criar_aula(dados):
    payload = {k: _s(v) for k, v in dados.items()}
    conflitos = _validar_aula(payload)
    if conflitos:
        return False, conflitos, ""

    aulas = read("aulas")
    novo_id = str(next_id("aulas", col="id_aula"))
    row = {
        "id_aula": novo_id,
        "id_professor": payload["id_professor"],
        "id_turma": payload["id_turma"],
        "id_sala": payload["id_sala"],
        "id_horario": payload["id_horario"],
        "id_disciplina": payload["id_disciplina"],
    }
    aulas = pd.concat([aulas, pd.DataFrame([row])], ignore_index=True)
    write("aulas", aulas[AULAS_COLS])
    return True, [], novo_id


def editar_aula(id_val, dados):
    aulas = read("aulas")
    idx = aulas[aulas["id_aula"] == _s(id_val)].index
    if idx.empty:
        return False, ["Aula não encontrada"]

    base = aulas.iloc[idx[0]].to_dict()
    for k, v in dados.items():
        if k in base:
            base[k] = _s(v)

    conflitos = _validar_aula(base, excluir_id=id_val)
    if conflitos:
        return False, conflitos

    for col in AULAS_COLS:
        aulas.at[idx[0], col] = _s(base.get(col, ""))
    write("aulas", aulas[AULAS_COLS])
    return True, []


def deletar_aula(id_val):
    aulas = read("aulas")
    aulas = aulas[aulas["id_aula"] != _s(id_val)]
    write("aulas", aulas[AULAS_COLS])


def get_grade():
    aulas = read("aulas")
    if aulas.empty:
        return []

    profs = _map_by_id(read("professores"))
    turmas = _map_by_id(read("turmas"))
    salas = _map_by_id(read("salas"))
    horarios = _map_by_id(read("horarios"))
    disciplinas = _map_by_id(read("disciplinas"))

    rows = []
    for _, a in aulas.iterrows():
        id_aula = _s(a.get("id_aula", ""))
        pid = _s(a.get("id_professor", ""))
        tid = _s(a.get("id_turma", ""))
        sid = _s(a.get("id_sala", ""))
        hid = _s(a.get("id_horario", ""))
        did = _s(a.get("id_disciplina", ""))
        p = profs.get(pid, {})
        t = turmas.get(tid, {})
        s = salas.get(sid, {})
        h = horarios.get(hid, {})
        d = disciplinas.get(did, {})
        rows.append({
            "id_aula": id_aula,
            "id_professor": pid,
            "id_turma": tid,
            "id_sala": sid,
            "id_horario": hid,
            "id_disciplina": did,
            "professor": _s(p.get("nome", pid)),
            "turma": _s(t.get("nome", tid)),
            "sala": _s(s.get("nome", sid)),
            "disciplina": _s(d.get("nome", did)),
            "curso": _s(t.get("curso", d.get("curso", ""))),
            "turno": _s(h.get("turno", t.get("periodo", ""))),
            "dia": _s(h.get("dia_semana", "")),
            "inicio": _s(h.get("horario_inicio", "")),
            "fim": _s(h.get("horario_fim", "")),
        })

    rows = sorted(rows, key=lambda r: (DIAS_ORD.get(_s(r.get("dia", "")), 99), _s(r.get("inicio", "")), _s(r.get("id_aula", ""))))
    return rows


def get_resumo():
    professores = read("professores")
    turmas = read("turmas")
    disciplinas = read("disciplinas")
    salas = read("salas")
    aulas = read("aulas")
    alunos = 0
    if not turmas.empty and "quantidade_alunos" in turmas.columns:
        alunos = int(pd.to_numeric(turmas["quantidade_alunos"], errors="coerce").fillna(0).sum())
    return {
        "professores": int(len(professores.index)),
        "turmas": int(len(turmas.index)),
        "disciplinas": int(len(disciplinas.index)),
        "salas": int(len(salas.index)),
        "aulas": int(len(aulas.index)),
        "alunos": alunos,
    }


def gerar_grade():
    professores = read("professores")
    disciplinas = read("disciplinas")
    turmas = read("turmas")
    salas = read("salas")
    horarios = read("horarios")

    if professores.empty or disciplinas.empty or turmas.empty or salas.empty or horarios.empty:
        write("aulas", pd.DataFrame(columns=AULAS_COLS))
        return {"ok": False, "msg": "Cadastros insuficientes para gerar a grade.", "turmas_sem": []}

    prof_disciplinas = _disciplinas_por_professor(professores, disciplinas)
    prof_info = {}
    for _, p in professores.iterrows():
        pid = _s(p.get("id", ""))
        if not pid:
            continue
        dias = set(_split_ids(p.get("dias_disponiveis", "")))
        max_dia = _i(p.get("max_aulas_dia", "4"), 4)
        if max_dia <= 0:
            max_dia = 4
        prof_info[pid] = {
            "dias": dias,
            "max_dia": max_dia,
            "disciplinas": set(prof_disciplinas.get(pid, set())),
        }

    disc_map = _map_by_id(disciplinas)
    salas_list = salas.to_dict("records")
    salas_list = sorted(salas_list, key=lambda s: (_i(s.get("capacidade", "0"), 0), _s(s.get("id", ""))))

    janelas_manha = _janelas_2x2(_ord_horarios(horarios, "Manha"))
    janelas_noite = _janelas_2x2(_ord_horarios(horarios, "Noite"))
    janelas_all = _janelas_2x2(_ord_horarios(horarios))

    turmas_list = turmas.to_dict("records")
    turmas_list = sorted(
        turmas_list,
        key=lambda t: (
            len(_disciplinas_por_turma(t, disciplinas)),
            _i(t.get("quantidade_alunos", "0"), 0),
            _s(t.get("id", "")),
        ),
        reverse=True,
    )

    ocup_prof = defaultdict(set)
    ocup_turma = defaultdict(set)
    ocup_sala = defaultdict(set)
    carga_dia_prof = defaultdict(int)
    carga_total_prof = defaultdict(int)

    aulas_rows = []
    prox_id = 1
    turmas_sem = set()

    for turma in turmas_list:
        tid = _s(turma.get("id", ""))
        tnome = _s(turma.get("nome", tid))
        turno = _s(turma.get("periodo", ""))
        qtd = _i(turma.get("quantidade_alunos", "0"), 0)

        if turno == "Manha":
            janelas_turno = janelas_manha
        elif turno == "Noite":
            janelas_turno = janelas_noite
        else:
            janelas_turno = janelas_all

        exigidas = _disciplinas_por_turma(turma, disciplinas)
        pendentes = _blocos_pendentes(exigidas, disc_map)
        if not pendentes or not janelas_turno:
            turmas_sem.add(tnome)
            continue

        while len(pendentes) >= 2:
            achou = None
            pares = _pares_pendentes(pendentes)
            if not pares:
                break

            for dia, bloco1, bloco2 in janelas_turno:
                hids1 = [_s(h.get("id", "")) for h in bloco1]
                hids2 = [_s(h.get("id", "")) for h in bloco2]
                hids = hids1 + hids2
                if len([h for h in hids if h]) != 4:
                    continue
                if any(tid in ocup_turma[hid] for hid in hids):
                    continue
                sid = _escolher_sala_bloco(salas_list, ocup_sala, hids, qtd)
                if not sid:
                    continue

                for idx1, idx2 in pares:
                    did1 = pendentes[idx1]
                    did2 = pendentes[idx2]
                    pid1 = _escolher_prof_bloco(did1, hids1, dia, prof_info, ocup_prof, carga_dia_prof, carga_total_prof)
                    if not pid1:
                        continue
                    extra = {pid1: len(hids1)}
                    pid2 = _escolher_prof_bloco(did2, hids2, dia, prof_info, ocup_prof, carga_dia_prof, carga_total_prof, extra=extra)
                    if not pid2:
                        continue
                    achou = (idx1, idx2, dia, hids1, hids2, did1, did2, pid1, pid2, sid)
                    break

                if achou:
                    break

            if not achou:
                break

            idx1, idx2, dia, hids1, hids2, did1, did2, pid1, pid2, sid = achou
            for hid in hids1:
                aulas_rows.append({
                    "id_aula": str(prox_id),
                    "id_professor": pid1,
                    "id_turma": tid,
                    "id_sala": sid,
                    "id_horario": hid,
                    "id_disciplina": _s(did1),
                })
                prox_id += 1
                ocup_prof[hid].add(pid1)
                ocup_turma[hid].add(tid)
                ocup_sala[hid].add(sid)
                carga_dia_prof[(pid1, dia)] += 1
                carga_total_prof[pid1] += 1
            for hid in hids2:
                aulas_rows.append({
                    "id_aula": str(prox_id),
                    "id_professor": pid2,
                    "id_turma": tid,
                    "id_sala": sid,
                    "id_horario": hid,
                    "id_disciplina": _s(did2),
                })
                prox_id += 1
                ocup_prof[hid].add(pid2)
                ocup_turma[hid].add(tid)
                ocup_sala[hid].add(sid)
                carga_dia_prof[(pid2, dia)] += 1
                carga_total_prof[pid2] += 1

            for idx in sorted([idx1, idx2], reverse=True):
                pendentes.pop(idx)

        if pendentes:
            turmas_sem.add(tnome)

    df_aulas = pd.DataFrame(aulas_rows, columns=AULAS_COLS)
    write("aulas", df_aulas)

    return {
        "ok": True,
        "msg": f"Grade 2x2 gerada com {len(aulas_rows)} aulas.",
        "turmas_sem": sorted([t for t in turmas_sem if t]),
    }


def exportar(tipo, filtro=""):
    rows = get_grade()
    val = _s(filtro)
    if tipo == "turma" and val:
        rows = [r for r in rows if _s(r.get("id_turma", "")) == val]
    if tipo == "professor" and val:
        rows = [r for r in rows if _s(r.get("id_professor", "")) == val]
    return rows
