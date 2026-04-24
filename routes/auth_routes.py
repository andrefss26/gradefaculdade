from flask import Blueprint, request, jsonify, session, redirect
from services.csv_service import read, write

auth_bp = Blueprint("auth", __name__)

def _user_session(row):
    return {"id":row["id"],"nome":row["nome"],"email":row["email"],
            "perfil":row["perfil"],"id_vinculo":row.get("id_vinculo","")}

@auth_bp.route("/login")
def login_page():
    from flask import render_template
    return render_template("login.html")

@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    d = request.get_json(force=True)
    email = d.get("email","").strip().lower()
    senha = d.get("senha","")
    users = read("usuarios")
    row   = users[(users["email"].str.lower() == email) & (users["senha"] == senha)]
    if row.empty:
        return jsonify({"ok":False,"msg":"Credenciais inválidas."}), 401
    u = row.iloc[0]
    session["user"] = _user_session(u)
    return jsonify({"ok":True,"perfil":u["perfil"]})

@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear(); return jsonify({"ok":True})

@auth_bp.route("/api/senha", methods=["PUT"])
def api_senha():
    if "user" not in session: return jsonify({"ok":False,"msg":"Não autenticado."}), 401
    d   = request.get_json(force=True)
    atual = d.get("senha_atual",""); nova = d.get("senha_nova","")
    users = read("usuarios"); uid = session["user"]["id"]
    idx   = users[(users["id"] == str(uid)) & (users["senha"] == atual)].index
    if idx.empty: return jsonify({"ok":False,"msg":"Senha atual incorreta."}), 400
    users.at[idx[0],"senha"] = nova; write("usuarios", users)
    return jsonify({"ok":True})
