"""
Rotas da grade horária.
Cobre: visualização da grade, CRUD de aulas, verificação de conflitos
e exportação CSV.
"""
import io
from datetime import datetime
import pandas as pd
from flask import Blueprint, request, jsonify, session, redirect, url_for, send_file
from services.grade_service import (
    obter_grade,
    verificar_conflitos,
    criar_aula,
    editar_aula,
    deletar_aula,
    exportar_grade,
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
