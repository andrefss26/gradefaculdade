from flask import Blueprint, jsonify, session, redirect, render_template
from services.grade_service import obter_resumo

dashboard_bp = Blueprint("dashboard", __name__)

def _user(): return session.get("user", {})

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def dashboard():
    if not _user(): return redirect("/login")
    u = _user()
    start = "grade" if u.get("perfil") in ("professor","aluno") else "dashboard"
    return render_template("index.html", user=u, start_page=start)

@dashboard_bp.route("/api/resumo")
def api_resumo():
    u = _user()
    if not u: return jsonify({}), 401
    try: return jsonify(obter_resumo(u))
    except Exception as e: return jsonify({"erro":str(e)}), 403
