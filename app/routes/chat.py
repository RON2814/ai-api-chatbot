from flask import Blueprint, jsonify

# Define the Blueprint
chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    return jsonify({"message": "Chat endpoint is ready!"})
