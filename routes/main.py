import io
from datetime import datetime
from functools import wraps

import pandas as pd
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file

from services.grade import check_conflitos, criar_aula, editar_aula, deletar_aula, get_grade, get_resumo, gerar_grade, exportar
from services.crud  import listar, criar, atualizar, deletar

bp = Blueprint("main", __name__)

def rl(f):
    @wraps(f)
    def inner(*a, **kw):
        if "user" not in session:
            return redirect(url_for("auth.pg_login"))
        return f(*a, **kw)
    return inner


# ── Pages ──────────────────────────────────────────────────────────────────────

@bp.route("/dashboard")
@rl
def dashboard():
    return render_template("index.html", user=session["user"])


# ── Resumo ─────────────────────────────────────────────────────────────────────

@bp.route("/api/resumo")
@rl
def api_resumo():
    return jsonify(get_resumo())


# ── CRUD genérico ──────────────────────────────────────────────────────────────

@bp.route("/api/<ent>", methods=["GET"])
@rl
def api_list(ent):
    return jsonify(listar(ent))

@bp.route("/api/<ent>", methods=["POST"])
@rl
def api_create(ent):
    try:
        novo = criar(ent, request.json)
        return jsonify({"ok": True, "id": novo["id"]})
    except ValueError as e:
        return jsonify({"ok": False, "msg": str(e)}), 400

@bp.route("/api/<ent>/<id_val>", methods=["PUT"])
@rl
def api_update(ent, id_val):
    try:
        ok = atualizar(ent, id_val, request.json)
    except ValueError as e:
        return jsonify({"ok": False, "msg": str(e)}), 400
    if not ok:
        return jsonify({"ok": False, "msg": "Registro não encontrado"}), 404
    return jsonify({"ok": True})

@bp.route("/api/<ent>/<id_val>", methods=["DELETE"])
@rl
def api_delete(ent, id_val):
    deletar(ent, id_val)
    return jsonify({"ok": True})


# ── Grade ──────────────────────────────────────────────────────────────────────

@bp.route("/api/grade")
@rl
def api_grade():
    return jsonify(get_grade())

@bp.route("/api/verificar_conflito", methods=["POST"])
@rl
def api_conflito():
    d = request.json
    ex = d.pop("excluir_id", "")
    return jsonify({"conflitos": check_conflitos(d, excluir_id=ex)})

@bp.route("/api/aulas", methods=["POST"])
@rl
def api_criar_aula():
    ok, conflitos, id_aula = criar_aula(request.json)
    if ok:
        return jsonify({"ok": True, "id_aula": id_aula})
    return jsonify({"ok": False, "conflitos": conflitos}), 409

@bp.route("/api/aulas/<id_val>", methods=["PUT"])
@rl
def api_editar_aula(id_val):
    dados = request.json; dados.pop("excluir_id", None)
    ok, conflitos = editar_aula(id_val, dados)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "conflitos": conflitos}), 409

@bp.route("/api/aulas/<id_val>", methods=["DELETE"])
@rl
def api_del_aula(id_val):
    deletar_aula(id_val)
    return jsonify({"ok": True})

@bp.route("/api/gerar_grade", methods=["POST"])
@rl
def api_gerar():
    return jsonify(gerar_grade())

@bp.route("/api/exportar/<tipo>")
@rl
def api_exportar(tipo):
    filtro = request.args.get("valor", "")
    rows   = exportar(tipo, filtro)
    buf    = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    buf.seek(0)
    nome = f"grade_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return send_file(io.BytesIO(buf.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name=nome)
