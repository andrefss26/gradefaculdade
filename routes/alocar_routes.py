from flask import Blueprint, jsonify, session
from services.alocar_service import alocar_grade_completa, relatorio_alocacao

alocar_bp = Blueprint("alocar", __name__)
def _u(): return session.get("user",{})

def _avisos(msg):
    if "⚠️" not in msg: return []
    try:
        parte = msg.split("⚠️",1)[1]
        if ":" in parte: parte = parte.split(":",1)[1]
        return [a.strip() for a in parte.split("|") if a.strip()]
    except: return []

@alocar_bp.route("/api/alocar-completo", methods=["POST"])
def api_alocar():
    u = _u()
    if not u: return jsonify({"sucesso":False,"mensagem":"Não autenticado."}), 401
    if u.get("perfil") != "admin":
        return jsonify({"sucesso":False,"mensagem":"Acesso negado."}), 403
    try:
        ok, msg, criadas = alocar_grade_completa(u)
    except PermissionError as e: return jsonify({"sucesso":False,"mensagem":str(e)}), 403
    except Exception as e:       return jsonify({"sucesso":False,"mensagem":f"Erro: {e}"}), 500
    if not ok:
        return jsonify({"sucesso":False,"mensagem":msg,"avisos":_avisos(msg)})
    return jsonify({
        "sucesso":True,"mensagem":msg,
        "total_aulas":           len(criadas),
        "turmas_atendidas":      len({a["turma"]      for a in criadas}),
        "disciplinas_atendidas": len({a["disciplina"] for a in criadas}),
        "avisos":                _avisos(msg),
    })

@alocar_bp.route("/api/relatorio-alocacao")
def api_relatorio():
    u = _u()
    if not u: return jsonify({}), 401
    if u.get("perfil") not in ("admin","coordenador"):
        return jsonify({"erro":"Acesso negado."}), 403
    try: return jsonify(relatorio_alocacao())
    except Exception as e: return jsonify({"erro":str(e)}), 500
