from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions within create_app to avoid circular import
    db.init_app(app)
    login_manager.init_app(app)

    # Import and register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
