from flask import Flask
from config import SECRET_KEY
from services.db   import init_csvs
from services.seed import seed
from routes.auth   import bp as auth_bp
from routes.main   import bp as main_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    return app


if __name__ == "__main__":
    init_csvs()
    seed()
    create_app().run(debug=True, port=5050)
