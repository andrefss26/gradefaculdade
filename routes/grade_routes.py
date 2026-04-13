"""
Rotas da grade horária.
Cobre: visualização da grade, CRUD de aulas, verificação de conflitos
e exportação CSV.
"""
import io
from datetime import datetime
import pandas as pd
from flask import Blueprint, request, jsonify, session, redirect, url_for, send_file, render_template
from services.grade_service import (
    obter_grade,
    verificar_conflitos,
    criar_aula,
    editar_aula,
    deletar_aula,
    limpar_grade,
    exportar_grade,
    alocar_aulas_automaticamente,
)

grade_bp = Blueprint("grade", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


# ── Grade visual ──────────────────────────────────────────────────────────────

@grade_bp.route("/grade")
@login_required
def grade_page():
    return render_template("index.html", user=session["user"], start_page="grade")


@grade_bp.route("/api/grade")
@login_required
def api_grade():
    return jsonify(obter_grade())


# ── Verificação de conflitos (tempo real) ─────────────────────────────────────

@grade_bp.route("/api/verificar_conflito", methods=["POST"])
@login_required
def api_verificar_conflito():
    data      = request.json
    excluir   = data.pop("excluir_id", "")
    conflitos = verificar_conflitos(data, excluir_id=excluir)
    return jsonify({"conflitos": conflitos})


# ── CRUD de Aulas ─────────────────────────────────────────────────────────────

@grade_bp.route("/api/aulas", methods=["POST"])
@login_required
def api_criar_aula():
    dados = request.json
    ok, conflitos, id_aula = criar_aula(dados)
    if ok:
        return jsonify({"ok": True, "id_aula": id_aula})
    return jsonify({"ok": False, "conflitos": conflitos}), 409


@grade_bp.route("/api/aulas/<id_val>", methods=["PUT"])
@login_required
def api_editar_aula(id_val):
    dados = request.json
    dados.pop("excluir_id", None)
    ok, conflitos = editar_aula(id_val, dados)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "conflitos": conflitos}), 409


@grade_bp.route("/api/aulas/<id_val>", methods=["DELETE"])
@login_required
def api_deletar_aula(id_val):
    deletar_aula(id_val)
    return jsonify({"ok": True})

@grade_bp.route("/api/grade/limpar", methods=["POST"])
@login_required
def api_limpar_grade():
    limpar_grade()
    return jsonify({"ok": True})


@grade_bp.route("/api/alocar-todos", methods=["POST"])
@login_required
def api_alocar_todos():
    from services.csv_service import read
    discs = read("disciplinas")
    total_alocadas = 0
    total_tentativas = 0
    for _, disc in discs.iterrows():
        total_tentativas += 1
        ok, msg, aulas = alocar_aulas_automaticamente(str(disc["id"]))
        if ok:
            total_alocadas += len(aulas)
    return jsonify({
        "ok": True,
        "msg": f"Alocadas {total_alocadas} aula(s) em {total_tentativas} disciplina(s).",
    })


# ── Exportação CSV ────────────────────────────────────────────────────────────

@grade_bp.route("/api/exportar/<tipo>")
@login_required
def api_exportar(tipo):
    filtro = request.args.get("valor", "")
    rows   = exportar_grade(tipo, filtro)
    df_out = pd.DataFrame(rows)
    buf    = io.StringIO()
    df_out.to_csv(buf, index=False)
    buf.seek(0)
    nome_arquivo = f"grade_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return send_file(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=nome_arquivo,
    )

# ── Alocação Automática ───────────────────────────────────────────────────────

@grade_bp.route("/api/alocar-automatico/<id_disc>", methods=["POST"])
@login_required
def api_alocar_automatico(id_disc):
    ok, msg, aulas = alocar_aulas_automaticamente(id_disc)
    if ok:
        return jsonify({"ok": True, "msg": msg, "aulas": aulas})
    return jsonify({"ok": False, "msg": msg}), 400