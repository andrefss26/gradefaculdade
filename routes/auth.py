from functools import wraps
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from services.auth import login, trocar_senha

bp = Blueprint("auth", __name__)

def require_login(f):
    @wraps(f)
    def inner(*a, **kw):
        if "user" not in session:
            return redirect(url_for("auth.pg_login"))
        return f(*a, **kw)
    return inner

@bp.route("/")
def index():
    return redirect(url_for("auth.pg_login") if "user" not in session else url_for("main.dashboard"))

@bp.route("/login")
def pg_login():
    return render_template("login.html")

@bp.route("/api/login", methods=["POST"])
def api_login():
    d = request.json
    u = login(d.get("email",""), d.get("senha",""))
    if not u:
        return jsonify({"ok": False, "msg": "Credenciais inválidas"}), 401
    session["user"] = u
    return jsonify({"ok": True, "user": u})

@bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})

@bp.route("/api/senha", methods=["PUT"])
@require_login
def api_senha():
    d = request.json
    ok, msg = trocar_senha(session["user"]["email"], d.get("atual",""), d.get("nova",""))
    return jsonify({"ok": ok, "msg": msg})
