from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import pandas as pd
import csv
import os
import json
import io
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "escola_secret_2025"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ── CSV paths ──────────────────────────────────────────────────────────────────
CSVS = {
    "professores": os.path.join(DATA_DIR, "professores.csv"),
    "disciplinas":  os.path.join(DATA_DIR, "disciplinas.csv"),
    "turmas":       os.path.join(DATA_DIR, "turmas.csv"),
    "salas":        os.path.join(DATA_DIR, "salas.csv"),
    "horarios":     os.path.join(DATA_DIR, "horarios.csv"),
    "aulas":        os.path.join(DATA_DIR, "aulas.csv"),
    "usuarios":     os.path.join(DATA_DIR, "usuarios.csv"),
}

HEADERS = {
    "professores": ["id","nome","email","dias_disponiveis","max_aulas_dia"],
    "disciplinas":  ["id","nome","carga_horaria","id_professor"],
    "turmas":       ["id","nome","quantidade_alunos"],
    "salas":        ["id","nome","capacidade","tipo"],
    "horarios":     ["id","turno","dia_semana","horario_inicio","horario_fim"],
    "aulas":        ["id_aula","id_professor","id_turma","id_sala","id_horario","id_disciplina"],
    "usuarios":     ["id","nome","email","senha","perfil"],
}

def init_csv():
    os.makedirs(DATA_DIR, exist_ok=True)
    for key, path in CSVS.items():
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(HEADERS[key])
    # seed admin user
    users = read_csv("usuarios")
    if users.empty:
        df = pd.DataFrame([{
            "id": 1, "nome": "Administrador", "email": "admin@escola.com",
            "senha": "admin123", "perfil": "adm"
        }])
        df.to_csv(CSVS["usuarios"], index=False)
    # seed demo data
    if read_csv("professores").empty:
        seed_demo()

def seed_demo():
    pd.DataFrame([
        {"id":1,"nome":"Carlos Souza","email":"carlos@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Quinta,Sexta","max_aulas_dia":4},
        {"id":2,"nome":"Ana Lima","email":"ana@escola.com","dias_disponiveis":"Segunda,Terca,Quinta,Sexta","max_aulas_dia":3},
        {"id":3,"nome":"Roberto Nunes","email":"roberto@escola.com","dias_disponiveis":"Segunda,Quarta,Sexta","max_aulas_dia":4},
    ]).to_csv(CSVS["professores"], index=False)

    pd.DataFrame([
        {"id":1,"nome":"Matematica","carga_horaria":4,"id_professor":1},
        {"id":2,"nome":"Portugues","carga_horaria":4,"id_professor":2},
        {"id":3,"nome":"Fisica","carga_horaria":3,"id_professor":3},
        {"id":4,"nome":"Historia","carga_horaria":2,"id_professor":2},
    ]).to_csv(CSVS["disciplinas"], index=False)

    pd.DataFrame([
        {"id":1,"nome":"1 EM A","quantidade_alunos":35},
        {"id":2,"nome":"2 EM B","quantidade_alunos":32},
        {"id":3,"nome":"3 EM C","quantidade_alunos":28},
    ]).to_csv(CSVS["turmas"], index=False)

    pd.DataFrame([
        {"id":1,"nome":"Sala 01","capacidade":40,"tipo":"Sala de Aula"},
        {"id":2,"nome":"Sala 02","capacidade":40,"tipo":"Sala de Aula"},
        {"id":3,"nome":"Lab. Informatica","capacidade":30,"tipo":"Laboratorio"},
    ]).to_csv(CSVS["salas"], index=False)

    horarios = []
    dias = ["Segunda","Terca","Quarta","Quinta","Sexta"]
    manha = [("07:00","07:50"),("07:50","08:40"),("08:40","09:30"),("09:40","10:30")]
    noite = [("19:00","19:50"),("19:50","20:40"),("20:40","21:30"),("21:40","22:30")]
    hid = 1
    for dia in dias:
        for ini, fim in manha:
            horarios.append({"id":hid,"turno":"Manha","dia_semana":dia,"horario_inicio":ini,"horario_fim":fim})
            hid += 1
        for ini, fim in noite:
            horarios.append({"id":hid,"turno":"Noite","dia_semana":dia,"horario_inicio":ini,"horario_fim":fim})
            hid += 1
    pd.DataFrame(horarios).to_csv(CSVS["horarios"], index=False)

    pd.DataFrame([], columns=HEADERS["aulas"]).to_csv(CSVS["aulas"], index=False)

    pd.DataFrame([
        {"id":1,"nome":"Administrador","email":"admin@escola.com","senha":"admin123","perfil":"adm"},
        {"id":2,"nome":"Carlos Souza","email":"carlos@escola.com","senha":"carlos123","perfil":"professor"},
        {"id":3,"nome":"Coord. Maria","email":"coord@escola.com","senha":"coord123","perfil":"coordenador"},
    ]).to_csv(CSVS["usuarios"], index=False)

def read_csv(key):
    try:
        df = pd.read_csv(CSVS[key], dtype=str)
        return df.fillna("")
    except:
        return pd.DataFrame(columns=HEADERS[key])

def write_csv(key, df):
    df.to_csv(CSVS[key], index=False)

def next_id(df, col="id"):
    if df.empty or col not in df.columns:
        return 1
    ids = pd.to_numeric(df[col], errors="coerce").dropna()
    return int(ids.max()) + 1 if not ids.empty else 1

# ── Auth ───────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return redirect(url_for("dashboard"))

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    df = read_csv("usuarios")
    user = df[(df["email"] == data.get("email","")) & (df["senha"] == data.get("senha",""))]
    if user.empty:
        return jsonify({"ok": False, "msg": "Credenciais inválidas"}), 401
    u = user.iloc[0].to_dict()
    session["user"] = u
    return jsonify({"ok": True, "user": u})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html", user=session["user"])

# ── API: Summary ───────────────────────────────────────────────────────────────
@app.route("/api/resumo")
@login_required
def api_resumo():
    profs   = read_csv("professores")
    turmas  = read_csv("turmas")
    discs   = read_csv("disciplinas")
    salas   = read_csv("salas")
    aulas   = read_csv("aulas")
    total_alunos = 0
    if not turmas.empty and "quantidade_alunos" in turmas.columns:
        total_alunos = pd.to_numeric(turmas["quantidade_alunos"], errors="coerce").fillna(0).sum()
    return jsonify({
        "professores": len(profs),
        "turmas": len(turmas),
        "disciplinas": len(discs),
        "salas": len(salas),
        "aulas": len(aulas),
        "alunos": int(total_alunos),
    })

# ── API: CRUD genérico ─────────────────────────────────────────────────────────
@app.route("/api/<entidade>", methods=["GET"])
@login_required
def get_all(entidade):
    if entidade not in CSVS:
        return jsonify([])
    df = read_csv(entidade)
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/<entidade>", methods=["POST"])
@login_required
def create_item(entidade):
    if entidade not in CSVS:
        return jsonify({"ok": False}), 404
    df = read_csv(entidade)
    data = request.json
    data["id"] = str(next_id(df))
    new_row = pd.DataFrame([data])
    df = pd.concat([df, new_row], ignore_index=True)
    write_csv(entidade, df)
    return jsonify({"ok": True, "id": data["id"]})

@app.route("/api/<entidade>/<id_val>", methods=["PUT"])
@login_required
def update_item(entidade, id_val):
    if entidade not in CSVS:
        return jsonify({"ok": False}), 404
    df = read_csv(entidade)
    id_col = "id_aula" if entidade == "aulas" else "id"
    idx = df[df[id_col] == str(id_val)].index
    if idx.empty:
        return jsonify({"ok": False, "msg": "Não encontrado"}), 404
    data = request.json
    for k, v in data.items():
        if k in df.columns:
            df.at[idx[0], k] = str(v)
    write_csv(entidade, df)
    return jsonify({"ok": True})

@app.route("/api/<entidade>/<id_val>", methods=["DELETE"])
@login_required
def delete_item(entidade, id_val):
    if entidade not in CSVS:
        return jsonify({"ok": False}), 404
    df = read_csv(entidade)
    id_col = "id_aula" if entidade == "aulas" else "id"
    df = df[df[id_col] != str(id_val)]
    write_csv(entidade, df)
    return jsonify({"ok": True})

# ── API: Grade / Conflito ──────────────────────────────────────────────────────
@app.route("/api/grade")
@login_required
def api_grade():
    aulas   = read_csv("aulas")
    profs   = read_csv("professores")
    turmas  = read_csv("turmas")
    salas   = read_csv("salas")
    hors    = read_csv("horarios")
    discs   = read_csv("disciplinas")

    if aulas.empty:
        return jsonify([])

    def lookup(df, id_col, id_val, field):
        row = df[df[id_col] == str(id_val)]
        return row.iloc[0][field] if not row.empty else id_val

    result = []
    for _, row in aulas.iterrows():
        h = hors[hors["id"] == str(row["id_horario"])]
        if h.empty:
            continue
        h = h.iloc[0]
        result.append({
            "id_aula":    row["id_aula"],
            "professor":  lookup(profs,  "id", row["id_professor"],  "nome"),
            "turma":      lookup(turmas, "id", row["id_turma"],      "nome"),
            "sala":       lookup(salas,  "id", row["id_sala"],       "nome"),
            "disciplina": lookup(discs,  "id", row["id_disciplina"], "nome"),
            "dia":        h["dia_semana"],
            "inicio":     h["horario_inicio"],
            "fim":        h["horario_fim"],
            "turno":      h["turno"],
            "id_professor":  row["id_professor"],
            "id_turma":      row["id_turma"],
            "id_sala":       row["id_sala"],
            "id_horario":    row["id_horario"],
            "id_disciplina": row["id_disciplina"],
        })
    return jsonify(result)

@app.route("/api/verificar_conflito", methods=["POST"])
@login_required
def verificar_conflito():
    data     = request.json
    aulas    = read_csv("aulas")
    excluir  = str(data.get("excluir_id", ""))
    if not aulas.empty and excluir:
        aulas = aulas[aulas["id_aula"] != excluir]

    conflitos = []
    for _, row in aulas.iterrows():
        if row["id_horario"] == str(data["id_horario"]):
            if row["id_professor"] == str(data["id_professor"]):
                conflitos.append("Professor já possui aula neste horário.")
            if row["id_turma"] == str(data["id_turma"]):
                conflitos.append("Turma já possui aula neste horário.")
            if row["id_sala"] == str(data["id_sala"]):
                conflitos.append("Sala já está ocupada neste horário.")
    return jsonify({"conflitos": list(set(conflitos))})

@app.route("/api/aulas", methods=["POST"])
@login_required
def criar_aula():
    data = request.json
    # verifica conflito
    check = verificar_conflito_interno(data)
    if check:
        return jsonify({"ok": False, "conflitos": check}), 409
    aulas = read_csv("aulas")
    data["id_aula"] = str(next_id(aulas, "id_aula"))
    new_row = pd.DataFrame([data])
    aulas = pd.concat([aulas, new_row], ignore_index=True)
    write_csv("aulas", aulas)
    return jsonify({"ok": True, "id_aula": data["id_aula"]})

@app.route("/api/aulas/<id_val>", methods=["PUT"])
@login_required
def editar_aula(id_val):
    data = request.json
    data["excluir_id"] = id_val
    check = verificar_conflito_interno(data)
    if check:
        return jsonify({"ok": False, "conflitos": check}), 409
    aulas = read_csv("aulas")
    idx = aulas[aulas["id_aula"] == str(id_val)].index
    if idx.empty:
        return jsonify({"ok": False}), 404
    for k, v in data.items():
        if k in aulas.columns:
            aulas.at[idx[0], k] = str(v)
    write_csv("aulas", aulas)
    return jsonify({"ok": True})

@app.route("/api/aulas/<id_val>", methods=["DELETE"])
@login_required
def deletar_aula(id_val):
    aulas = read_csv("aulas")
    aulas = aulas[aulas["id_aula"] != str(id_val)]
    write_csv("aulas", aulas)
    return jsonify({"ok": True})

def verificar_conflito_interno(data, excluir_id=None):
    aulas = read_csv("aulas")
    excluir = str(data.get("excluir_id", excluir_id or ""))
    if not aulas.empty and excluir:
        aulas = aulas[aulas["id_aula"] != excluir]
    conflitos = []
    for _, row in aulas.iterrows():
        if row["id_horario"] == str(data.get("id_horario","")):
            if row["id_professor"] == str(data.get("id_professor","")):
                conflitos.append("Professor já possui aula neste horário.")
            if row["id_turma"] == str(data.get("id_turma","")):
                conflitos.append("Turma já possui aula neste horário.")
            if row["id_sala"] == str(data.get("id_sala","")):
                conflitos.append("Sala já está ocupada neste horário.")
    return list(set(conflitos))

# ── API: Export CSV ────────────────────────────────────────────────────────────
@app.route("/api/exportar/<tipo>")
@login_required
def exportar(tipo):
    aulas   = read_csv("aulas")
    profs   = read_csv("professores")
    turmas  = read_csv("turmas")
    salas   = read_csv("salas")
    hors    = read_csv("horarios")
    discs   = read_csv("disciplinas")

    rows = []
    for _, row in aulas.iterrows():
        h = hors[hors["id"] == str(row["id_horario"])]
        if h.empty:
            continue
        h = h.iloc[0]
        prof  = profs[profs["id"]   == str(row["id_professor"])].iloc[0] if not profs[profs["id"]   == str(row["id_professor"])].empty else None
        turma = turmas[turmas["id"] == str(row["id_turma"])].iloc[0]      if not turmas[turmas["id"] == str(row["id_turma"])].empty else None
        sala  = salas[salas["id"]   == str(row["id_sala"])].iloc[0]       if not salas[salas["id"]   == str(row["id_sala"])].empty else None
        disc  = discs[discs["id"]   == str(row["id_disciplina"])].iloc[0] if not discs[discs["id"]   == str(row["id_disciplina"])].empty else None
        rows.append({
            "Turma":          turma["nome"] if turma is not None else "",
            "Professor":      prof["nome"]  if prof  is not None else "",
            "Disciplina":     disc["nome"]  if disc  is not None else "",
            "Sala":           sala["nome"]  if sala  is not None else "",
            "Tipo Sala":      sala["tipo"]  if sala  is not None else "",
            "Dia da Semana":  h["dia_semana"],
            "Horario Inicio": h["horario_inicio"],
            "Horario Fim":    h["horario_fim"],
            "Turno":          h["turno"],
        })

    df_out = pd.DataFrame(rows)

    if tipo == "turma":
        filtro = request.args.get("valor","")
        if filtro:
            df_out = df_out[df_out["Turma"] == filtro]
    elif tipo == "professor":
        filtro = request.args.get("valor","")
        if filtro:
            df_out = df_out[df_out["Professor"] == filtro]

    buf = io.StringIO()
    df_out.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"grade_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    )

# ── API: Senha ─────────────────────────────────────────────────────────────────
@app.route("/api/senha", methods=["PUT"])
@login_required
def alterar_senha():
    data  = request.json
    df    = read_csv("usuarios")
    email = session["user"]["email"]
    idx   = df[df["email"] == email].index
    if idx.empty:
        return jsonify({"ok": False}), 404
    if df.at[idx[0], "senha"] != data.get("atual",""):
        return jsonify({"ok": False, "msg": "Senha atual incorreta"}), 403
    df.at[idx[0], "senha"] = data.get("nova","")
    write_csv("usuarios", df)
    return jsonify({"ok": True})

if __name__ == "__main__":
    init_csv()
    app.run(debug=True, port=5050)
