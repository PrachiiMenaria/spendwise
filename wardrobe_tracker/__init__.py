from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # Load config
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.wardrobe_routes import wardrobe_bp
    from app.routes.expense_routes import expense_bp
    from app.routes.insight_routes import insight_bp
    from app.routes.user_routes import user_bp

    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(wardrobe_bp, url_prefix="/api/wardrobe")
    app.register_blueprint(expense_bp, url_prefix="/api/expenses")
    app.register_blueprint(insight_bp, url_prefix="/api")

    return app
