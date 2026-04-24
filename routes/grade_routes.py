from flask import Blueprint, request, jsonify, session, Response
from services.grade_service import (
    obter_grade, criar_aula, editar_aula, deletar_aula,
    limpar_grade, verificar_conflitos, exportar_grade,
)
import csv, io

grade_bp = Blueprint("grade", __name__)
def _u(): return session.get("user",{})

@grade_bp.route("/grade")
def grade_page():
    from flask import redirect
    if not _u(): return redirect("/login")
    from flask import render_template
    return render_template("index.html", user=_u(), start_page="grade")

@grade_bp.route("/api/grade")
def api_grade():
    u = _u()
    if not u: return jsonify([]), 401
    try: return jsonify(obter_grade(u))
    except Exception as e: return jsonify({"erro":str(e)}), 403

@grade_bp.route("/api/verificar_conflito", methods=["POST"])
def api_conflito():
    d = request.get_json(force=True)
    return jsonify({"conflitos": verificar_conflitos(d, d.get("excluir_id",""))})

@grade_bp.route("/api/aulas", methods=["POST"])
def api_criar_aula():
    u = _u()
    if not u: return jsonify({"ok":False}), 401
    d = request.get_json(force=True)
    try:
        ok, conflitos, id_aula = criar_aula(d, u)
        return jsonify({"ok":ok,"conflitos":conflitos,"id_aula":id_aula})
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}), 403

@grade_bp.route("/api/aulas/<id_aula>", methods=["PUT"])
def api_editar_aula(id_aula):
    u = _u()
    if not u: return jsonify({"ok":False}), 401
    d = request.get_json(force=True)
    try:
        ok, conflitos = editar_aula(id_aula, d, u)
        return jsonify({"ok":ok,"conflitos":conflitos})
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}), 403

@grade_bp.route("/api/aulas/<id_aula>", methods=["DELETE"])
def api_deletar_aula(id_aula):
    u = _u()
    if not u: return jsonify({"ok":False}), 401
    try: deletar_aula(id_aula, u); return jsonify({"ok":True})
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}), 403

@grade_bp.route("/api/limpar_grade", methods=["POST"])
def api_limpar_grade():
    u = _u()
    if not u: return jsonify({"ok":False}), 401
    try: limpar_grade(u); return jsonify({"ok":True})
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}), 403

@grade_bp.route("/api/exportar/<tipo>")
def api_exportar(tipo):
    u = _u()
    if not u: return jsonify([]), 401
    filtro = request.args.get("filtro","")
    try:
        rows = exportar_grade(tipo, u, filtro)
        if not rows: return Response("Sem dados.", mimetype="text/plain")
        buf = io.StringIO()
        w   = csv.DictWriter(buf, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition":f"attachment;filename=grade_{tipo}.csv"})
    except Exception as e: return jsonify({"erro":str(e)}), 403
