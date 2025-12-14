import os

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config


def create_app(config_class=Config):
    # Load environment variables from .env if present
    load_dotenv()

    # 1. Initialize the app
    app = Flask(__name__)

    # 2. Load configuration from config.py
    app.config.from_object(config_class)

    # Enable CORS(Allow all origins for now)
    CORS(app)

    # Register Blueprints
    from app.routes.chat import chat_bp
    app.register_blueprint(chat_bp)

    # Serve the frontend
    @app.route('/')
    def index():
        static_dir = os.path.join(app.root_path, 'static')
        return send_from_directory(static_dir, 'index.html')

    return app
