"""
Rotas de autenticação.
Cobre: login, logout e alteração de senha.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from services.auth_service import verificar_login, alterar_senha

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("auth.login_page"))
    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/login")
def login_page():
    return render_template("login.html")


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    data     = request.json
    usuario  = verificar_login(data.get("email", ""), data.get("senha", ""))
    if not usuario:
        return jsonify({"ok": False, "msg": "Credenciais inválidas"}), 401
    session["user"] = usuario
    return jsonify({"ok": True, "user": usuario})


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/api/senha", methods=["PUT"])
def api_senha():
    if "user" not in session:
        return jsonify({"ok": False}), 401
    data = request.json
    ok, msg = alterar_senha(
        email       = session["user"]["email"],
        senha_atual = data.get("atual", ""),
        senha_nova  = data.get("nova", ""),
    )
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "msg": msg}), 403
