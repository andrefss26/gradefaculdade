from flask import Blueprint, request, jsonify, session
from services.csv_service import read, write, next_id
from services.auth_service import verificar_permissao
import pandas as pd

cadastro_bp = Blueprint("cadastro", __name__)
ENTIDADES = ["professores","disciplinas","turmas","cursos","salas","horarios"]

def _u(): return session.get("user",{})

def _id_col(e):
    return "id_aula" if e == "aulas" else "id"

@cadastro_bp.route("/api/<entidade>")
def listar(entidade):
    if entidade not in ENTIDADES: return jsonify([])
    u = _u()
    try: verificar_permissao(u, entidade, "ler")
    except: return jsonify([]), 403
    return jsonify(read(entidade).to_dict("records"))

@cadastro_bp.route("/api/<entidade>", methods=["POST"])
def criar(entidade):
    if entidade not in ENTIDADES: return jsonify({"ok":False}), 404
    u = _u()
    try: verificar_permissao(u, entidade, "criar")
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}), 403
    d  = request.get_json(force=True); df = read(entidade)
    d["id"] = str(next_id(entidade,"id"))
    df = pd.concat([df, pd.DataFrame([d])], ignore_index=True)
    write(entidade, df); return jsonify({"ok":True,"id":d["id"]})

@cadastro_bp.route("/api/<entidade>/<id>", methods=["PUT"])
def editar(entidade, id):
    if entidade not in ENTIDADES: return jsonify({"ok":False}), 404
    u = _u()
    try: verificar_permissao(u, entidade, "editar", id_alvo=id)
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}), 403
    d  = request.get_json(force=True); df = read(entidade)
    idx = df[df["id"] == str(id)].index
    if idx.empty: return jsonify({"ok":False,"msg":"Não encontrado."}), 404
    for k,v in d.items():
        if k in df.columns: df.at[idx[0],k] = str(v)
    write(entidade, df); return jsonify({"ok":True})

@cadastro_bp.route("/api/<entidade>/<id>", methods=["DELETE"])
def deletar(entidade, id):
    if entidade not in ENTIDADES: return jsonify({"ok":False}), 404
    u = _u()
    try: verificar_permissao(u, entidade, "deletar")
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}), 403
    df = read(entidade); write(entidade, df[df["id"] != str(id)])
    return jsonify({"ok":True})

# Disponibilidade professor
@cadastro_bp.route("/api/professores/<id>/disponibilidade", methods=["PUT"])
def disponibilidade(id):
    u = _u()
    from services.grade_service import editar_disponibilidade
    d    = request.get_json(force=True)
    dias = d.get("dias",[])
    ok, msg = editar_disponibilidade(str(id), dias, u)
    return jsonify({"ok":ok,"msg":msg})
