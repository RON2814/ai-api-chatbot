from flask import Blueprint, jsonify, request, current_app, Response, stream_with_context
from openai import OpenAI
from google import generativeai as genai

# Define the Blueprint
chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "message is required"}), 400
    requested_provider = (data.get('provider') or '').strip().lower() or None
    requested_model = (data.get('model') or '').strip() or None

    openai_key = current_app.config.get('OPENAI_API_KEY')
    openai_model = current_app.config.get('OPENAI_MODEL')
    gemini_key = current_app.config.get('GEMINI_API_KEY')
    gemini_model = current_app.config.get('GEMINI_MODEL')

    # Prefer Gemini when configured, otherwise fall back to OpenAI
    def pick_provider():
        if requested_provider == 'gemini' and gemini_key:
            return 'gemini'
        if requested_provider == 'openai' and openai_key:
            return 'openai'
        if requested_provider:  # requested but not available
            return None
        # default priority: Gemini if configured, else OpenAI
        if gemini_key:
            return 'gemini'
        if openai_key:
            return 'openai'
        return None

    provider = pick_provider()
    if not provider:
        return jsonify({"error": "No API provider configured or available"}), 500

    if provider == 'gemini':
        model_name = requested_model or gemini_model
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                user_message,
                generation_config={"temperature": 0.7,
                                   "max_output_tokens": 2048},
            )
            reply = response.text or ""
            finish_reason = None
            try:
                if getattr(response, 'candidates', None):
                    finish_reason = response.candidates[0].finish_reason
            except Exception:
                finish_reason = None
            return jsonify({
                "reply": reply,
                "provider": 'gemini',
                "model": model_name,
                "finish_reason": finish_reason,
            })
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": "Failed to contact Gemini", "detail": str(exc)}), 502

    if provider == 'openai':
        model_name = requested_model or openai_model
        client = OpenAI(api_key=openai_key)
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a concise assistant."},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=2048,
            )

            reply = completion.choices[0].message.content
            finish_reason = None
            try:
                finish_reason = completion.choices[0].finish_reason
            except Exception:
                finish_reason = None
            return jsonify({
                "reply": reply,
                "provider": 'openai',
                "model": model_name,
                "finish_reason": finish_reason,
            })
        except Exception as exc:  # noqa: BLE001
            # Return a safe error to the client
            return jsonify({"error": "Failed to contact OpenAI", "detail": str(exc)}), 502

    return jsonify({"error": "No API provider configured"}), 500


@chat_bp.route('/api/stream', methods=['POST'])
def chat_stream():
    data = request.get_json(silent=True) or {}
    user_message = data.get('message')
    requested_provider = (data.get('provider') or '').strip().lower() or None
    requested_model = (data.get('model') or '').strip() or None

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    openai_key = current_app.config.get('OPENAI_API_KEY')
    openai_model = current_app.config.get('OPENAI_MODEL')
    gemini_key = current_app.config.get('GEMINI_API_KEY')
    gemini_model = current_app.config.get('GEMINI_MODEL')

    def pick_provider():
        if requested_provider == 'gemini' and gemini_key:
            return 'gemini'
        if requested_provider == 'openai' and openai_key:
            return 'openai'
        if requested_provider:
            return None
        if gemini_key:
            return 'gemini'
        if openai_key:
            return 'openai'
        return None

    provider = pick_provider()
    if not provider:
        return jsonify({"error": "No API provider configured or available"}), 500

    def sse(data_obj):
        import json
        return f"data: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

    @stream_with_context
    def generate():
        try:
            if provider == 'gemini':
                model_name = requested_model or gemini_model
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel(model_name)
                stream = model.generate_content(
                    user_message,
                    generation_config={"temperature": 0.7,
                                       "max_output_tokens": 2048},
                    stream=True,
                )
                full = []
                for chunk in stream:
                    delta = getattr(chunk, 'text', '') or ''
                    if delta:
                        full.append(delta)
                        yield sse({"delta": delta})
                # finalize
                try:
                    stream.resolve()
                except Exception:
                    pass
                finish_reason = None
                try:
                    if getattr(stream, 'candidates', None):
                        finish_reason = stream.candidates[0].finish_reason
                except Exception:
                    finish_reason = None
                yield sse({
                    "done": True,
                    "provider": 'gemini',
                    "model": model_name,
                    "finish_reason": finish_reason,
                })
                return

            if provider == 'openai':
                model_name = requested_model or openai_model
                client = OpenAI(api_key=openai_key)
                finish_reason = None
                with client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a concise assistant."},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                    max_tokens=2048,
                    stream=True,
                ) as stream:
                    for event in stream:
                        try:
                            choice = event.choices[0]
                            delta = getattr(choice.delta, 'content', None)
                            if delta:
                                yield sse({"delta": delta})
                            if getattr(choice, 'finish_reason', None):
                                finish_reason = choice.finish_reason
                        except Exception:
                            continue
                yield sse({
                    "done": True,
                    "provider": 'openai',
                    "model": model_name,
                    "finish_reason": finish_reason,
                })
        except Exception as exc:
            yield sse({"error": "stream_error", "detail": str(exc)})

    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'text/event-stream',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
    }
    return Response(generate(), headers=headers)
