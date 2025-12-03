from flask import Flask
from flask_cors import CORS
from config import Config


def create_app(config_class=Config):
    # 1. Initialize the app
    app = Flask(__name__)

    # 2. Load configuration from config.py
    app.config.from_object(config_class)

    # Enable CORS(Allow all origins for now)
    CORS(app)

    # Register Blueprints
    from app.routes.chat import chat_bp
    app.register_blueprint(chat_bp)

    # 3. Define a simple route (We will move this to Blueprints later)
    @app.route('/')
    def index():
        return "Hello from the Application Factory!"

    return app
