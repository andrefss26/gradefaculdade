"""
Rotas do dashboard.
Cobre: página principal e endpoint de resumo/totais.
"""
from flask import Blueprint, render_template, jsonify, session, redirect, url_for
from services.grade_service import obter_resumo

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html", user=session["user"])


@dashboard_bp.route("/api/resumo")
@login_required
def api_resumo():
    return jsonify(obter_resumo())
