"""Serviço da grade horária com controle de acesso."""
from __future__ import annotations
import pandas as pd
from services.csv_service import read, write, next_id
from services.auth_service import verificar_permissao

def _lookup(df, id_col, id_val, campo):
    row = df[df[id_col] == str(id_val)]
    return row.iloc[0][campo] if not row.empty else id_val

def _sort_horarios(hors):
    ordem = {"Segunda":1,"Terca":2,"Quarta":3,"Quinta":4,"Sexta":5,"Sabado":6,"Domingo":7}
    return hors.assign(
        dia_ord=[ordem.get(d, 99) for d in hors["dia_semana"]],
        inicio_ord=[int(t.replace(":","")) if isinstance(t,str) and ":" in t else 0 for t in hors["horario_inicio"]],
    ).sort_values(["dia_ord","inicio_ord"]).reset_index(drop=True)

def _get_horario_sequence(hors, start_id, blocos):
    if blocos <= 1:
        return [str(start_id)]
    hs = _sort_horarios(hors)
    idx = hs[hs["id"] == str(start_id)].index
    if idx.empty: return []
    pos = idx[0]; dia = hs.at[pos,"dia_semana"]; seq = []
    for off in range(blocos):
        p = pos + off
        if p >= len(hs): return []
        r = hs.iloc[p]
        if str(r["dia_semana"]) != str(dia): return []
        seq.append(str(r["id"]))
    return seq

def _get_disciplina_duracao(disc_id, discs):
    d = discs[discs["id"] == str(disc_id)]
    if d.empty: return 1
    try: return int(d.iloc[0].get("duracao_blocos",1) or 1)
    except: return 1

def _obter_seq(aula_row, horarios, discs):
    dur = _get_disciplina_duracao(aula_row.get("id_disciplina",""), discs)
    return set(_get_horario_sequence(horarios, aula_row.get("id_horario",""), dur))

def _montar_item(row, profs, turmas, salas, discs, hors):
    dur   = _get_disciplina_duracao(row["id_disciplina"], discs)
    slots = _get_horario_sequence(hors, row["id_horario"], dur)
    if not slots: return None
    f = hors[hors["id"] == slots[0]];  l = hors[hors["id"] == slots[-1]]
    if f.empty or l.empty: return None
    f = f.iloc[0]; l = l.iloc[0]
    return {
        "id_aula":      row["id_aula"],
        "professor":    _lookup(profs,  "id", row["id_professor"],  "nome"),
        "turma":        _lookup(turmas, "id", row["id_turma"],      "nome"),
        "sala":         _lookup(salas,  "id", row["id_sala"],       "nome"),
        "disciplina":   _lookup(discs,  "id", row["id_disciplina"], "nome"),
        "dia":          f["dia_semana"],
        "inicio":       f["horario_inicio"],
        "fim":          l["horario_fim"],
        "turno":        f["turno"],
        "id_professor": row["id_professor"],
        "id_turma":     row["id_turma"],
        "id_sala":      row["id_sala"],
        "id_horario":   row["id_horario"],
        "id_disciplina":row["id_disciplina"],
    }

def verificar_conflitos(dados, excluir_id=""):
    aulas = read("aulas")
    if not aulas.empty and excluir_id:
        aulas = aulas[aulas["id_aula"] != str(excluir_id)]
    hors = read("horarios"); discs = read("disciplinas")
    nova = set(_get_horario_sequence(hors, str(dados.get("id_horario","")),
                _get_disciplina_duracao(dados.get("id_disciplina",""), discs)))
    conflitos = set()
    for _, row in aulas.iterrows():
        ex = _obter_seq(row, hors, discs)
        if not nova or not ex or not nova.intersection(ex): continue
        if row["id_professor"] == str(dados.get("id_professor","")): conflitos.add("Professor já possui aula neste horário.")
        if row["id_turma"]     == str(dados.get("id_turma","")): conflitos.add("Turma já possui aula neste horário.")
        if row["id_sala"]      == str(dados.get("id_sala","")): conflitos.add("Sala já está ocupada neste horário.")
    return list(conflitos)

def criar_aula(dados, usuario):
    verificar_permissao(usuario, "aulas", "criar")
    c = verificar_conflitos(dados)
    if c: return False, c, ""
    aulas = read("aulas")
    dados["id_aula"] = str(next_id("aulas","id_aula"))
    aulas = pd.concat([aulas, pd.DataFrame([dados])], ignore_index=True)
    write("aulas", aulas)
    return True, [], dados["id_aula"]

def editar_aula(id_aula, dados, usuario):
    verificar_permissao(usuario, "aulas", "editar")
    c = verificar_conflitos(dados, excluir_id=id_aula)
    if c: return False, c
    aulas = read("aulas"); idx = aulas[aulas["id_aula"] == str(id_aula)].index
    if idx.empty: return False, ["Aula não encontrada."]
    for campo, valor in dados.items():
        if campo in aulas.columns: aulas.at[idx[0], campo] = str(valor)
    write("aulas", aulas); return True, []

def deletar_aula(id_aula, usuario):
    verificar_permissao(usuario, "aulas", "deletar")
    aulas = read("aulas")
    write("aulas", aulas[aulas["id_aula"] != str(id_aula)])
    return True

def limpar_grade(usuario):
    verificar_permissao(usuario, "aulas", "deletar")
    write("aulas", pd.DataFrame(columns=["id_aula","id_professor","id_turma","id_sala","id_horario","id_disciplina"]))
    return True

def editar_disponibilidade(id_professor, dias, usuario):
    verificar_permissao(usuario, "professores", "editar", id_alvo=id_professor)
    profs = read("professores"); idx = profs[profs["id"] == str(id_professor)].index
    if idx.empty: return False, "Professor não encontrado."
    validos = {"Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"}
    limpos  = [d.strip() for d in dias if d.strip() in validos]
    if not limpos: return False, "Nenhum dia válido informado."
    profs.at[idx[0], "dias_disponiveis"] = ",".join(limpos)
    write("professores", profs); return True, "Disponibilidade atualizada."

def obter_grade(usuario):
    uid    = str(usuario.get("id_professor") or usuario.get("id",""))
    verificar_permissao(usuario, "grade", "ler", id_alvo=uid)
    aulas  = read("aulas")
    if aulas.empty: return []
    perfil = usuario.get("perfil","")
    if perfil == "professor": aulas = aulas[aulas["id_professor"] == uid]
    elif perfil == "aluno":   aulas = aulas[aulas["id_turma"]     == uid]
    if aulas.empty: return []
    profs  = read("professores"); turmas = read("turmas")
    salas  = read("salas"); discs = read("disciplinas"); hors = read("horarios")
    return [item for _, row in aulas.iterrows()
            if (item := _montar_item(row, profs, turmas, salas, discs, hors))]

def obter_resumo(usuario):
    verificar_permissao(usuario, "dashboard", "ler")
    turmas = read("turmas"); total_alunos = 0
    if not turmas.empty and "quantidade_alunos" in turmas.columns:
        total_alunos = pd.to_numeric(turmas["quantidade_alunos"], errors="coerce").fillna(0).sum()
    return {
        "professores": len(read("professores")),
        "turmas":      len(turmas),
        "disciplinas": len(read("disciplinas")),
        "salas":       len(read("salas")),
        "aulas":       len(read("aulas")),
        "alunos":      int(total_alunos),
    }

def exportar_grade(tipo, usuario, filtro_valor=""):
    verificar_permissao(usuario, "grade", "exportar")
    aulas = read("aulas"); profs = read("professores"); turmas = read("turmas")
    salas = read("salas"); hors  = read("horarios");   discs  = read("disciplinas")
    rows = []
    for _, row in aulas.iterrows():
        seq = _get_horario_sequence(hors, str(row["id_horario"]),
                _get_disciplina_duracao(row.get("id_disciplina",""), discs))
        if not seq: continue
        f = hors[hors["id"] == seq[0]]; l = hors[hors["id"] == seq[-1]]
        if f.empty or l.empty: continue
        f = f.iloc[0]; l = l.iloc[0]
        pr = profs[profs["id"]   == str(row["id_professor"])]
        tr = turmas[turmas["id"] == str(row["id_turma"])]
        sa = salas[salas["id"]   == str(row["id_sala"])]
        di = discs[discs["id"]   == str(row["id_disciplina"])]
        rows.append({
            "Turma":          tr.iloc[0]["nome"]   if not tr.empty else "",
            "Professor":      pr.iloc[0]["nome"]   if not pr.empty else "",
            "Disciplina":     di.iloc[0]["nome"]   if not di.empty else "",
            "Sala":           sa.iloc[0]["nome"]   if not sa.empty else "",
            "Tipo Sala":      sa.iloc[0]["tipo"]   if not sa.empty else "",
            "Dia da Semana":  f["dia_semana"],
            "Horario Inicio": f["horario_inicio"],
            "Horario Fim":    l["horario_fim"],
            "Turno":          f["turno"],
        })
    if filtro_valor:
        campo = "Turma" if tipo == "turma" else "Professor"
        rows  = [r for r in rows if r[campo] == filtro_valor]
    return rows
