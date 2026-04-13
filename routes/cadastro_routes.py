"""
Rotas de cadastro (CRUD genérico).
Cobre: professores, disciplinas, turmas, salas e horários institucionais.
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for
from services.cadastro_service import listar, criar, atualizar, deletar

cadastro_bp = Blueprint("cadastro", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


@cadastro_bp.route("/api/<entidade>", methods=["GET"])
@login_required
def get_all(entidade):
    return jsonify(listar(entidade))


@cadastro_bp.route("/api/<entidade>", methods=["POST"])
@login_required
def create_item(entidade):
    dados = request.json
    try:
        novo = criar(entidade, dados)
        return jsonify({"ok": True, "id": novo["id"]})
    except ValueError as e:
        return jsonify({"ok": False, "msg": str(e)}), 400


@cadastro_bp.route("/api/<entidade>/<id_val>", methods=["PUT"])
@login_required
def update_item(entidade, id_val):
    dados = request.json
    ok = atualizar(entidade, id_val, dados)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "msg": "Registro não encontrado."}), 404


@cadastro_bp.route("/api/<entidade>/<id_val>", methods=["DELETE"])
@login_required
def delete_item(entidade, id_val):
    deletar(entidade, id_val)
    return jsonify({"ok": True})
