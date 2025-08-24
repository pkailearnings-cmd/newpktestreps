import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Basic config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change")
    os.makedirs(app.instance_path, exist_ok=True)

    # Database
    db_path = os.path.join(app.instance_path, "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Uploads
    upload_dir = os.path.join(app.instance_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir

    db.init_app(app)

    # Register blueprints
    from .routes import main_bp  # type: ignore
    app.register_blueprint(main_bp)

    # Create tables on first run
    with app.app_context():
        from . import models  # ensure models are imported
        db.create_all()

    return app