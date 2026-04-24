"""
app.py — Ponto de entrada do sistema GradeEscolar.
"""
from flask import Flask, redirect
from config import SECRET_KEY
from services.csv_service import init_csvs
from services.seed_service import seed_demo
from routes.auth_routes      import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.cadastro_routes  import cadastro_bp
from routes.grade_routes     import grade_bp
from routes.alocar_routes    import alocar_bp

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cadastro_bp)
    app.register_blueprint(grade_bp)
    app.register_blueprint(alocar_bp)
    return app

app = create_app()

if __name__ == "__main__":
    init_csvs()
    seed_demo()
    app.run(debug=True, port=5050)
