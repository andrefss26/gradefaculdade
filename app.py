"""
app.py — Ponto de entrada do sistema GradeEscolar.

Responsabilidade única: criar a aplicação Flask, registrar
os blueprints e inicializar os dados na primeira execução.
Nenhuma lógica de negócio deve residir aqui.
"""
from flask import Flask

from config import SECRET_KEY
from services.csv_service import init_csvs
from services.seed_service import seed_demo

from routes.auth_routes      import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.cadastro_routes  import cadastro_bp
from routes.grade_routes     import grade_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # ── Registra os módulos de rotas ──────────────────────────────────────────
    app.register_blueprint(auth_bp)       # /login  /api/login  /api/logout  /api/senha
    app.register_blueprint(dashboard_bp)  # /dashboard  /api/resumo
    app.register_blueprint(cadastro_bp)   # /api/<entidade>  (professores, turmas, etc.)
    app.register_blueprint(grade_bp)      # /api/grade  /api/aulas  /api/exportar

    return app


if __name__ == "__main__":
    # Garante que os CSVs existam e popula com dados de demo se necessário
    init_csvs()
    seed_demo()

    app = create_app()
    app.run(debug=True, port=5050)
