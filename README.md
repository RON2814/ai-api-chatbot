# AI API Chatbot (Flask)

Simple Flask-based chatbot that proxies requests to OpenAI. Ships with a minimal frontend at `/` that talks to the backend `/api/chat` endpoint.

## Requirements

-   Python 3.14+
-   OpenAI API key

## Setup

1. Clone or open this folder.
2. Create and activate a virtual environment (Windows PowerShell):

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If using Command Prompt: `\.venv\Scripts\activate.bat` 3) Install dependencies:

```
python -m pip install -r requirements.txt
```

4. Configure environment variables:

```
copy .env.example .env
```

Edit `.env` and set at least:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # or any model your account can access
SECRET_KEY=change-me
```

## Running the app

Following Flask 3.x guidance from https://flask.palletsprojects.com/en/stable/:

```
set FLASK_APP=run:app
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

-   On PowerShell, use `$env:FLASK_APP="run:app"` and `$env:FLASK_ENV="development"`.
-   The app loads `.env` automatically via `python-dotenv` when created.

Visit http://127.0.0.1:5000 to use the frontend. It POSTs to `/api/chat`.

## API

-   `POST /api/chat`
    -   Request JSON: `{ "message": "Hello" }`
    -   Response JSON: `{ "reply": "..." }` or `{ "error": "...", "detail": "..." }`

## Project layout

-   `run.py` — entrypoint
-   `config.py` — configuration (reads env vars)
-   `app/__init__.py` — app factory, loads `.env`, registers blueprints
-   `app/routes/chat.py` — `/api/chat` endpoint using OpenAI
-   `app/static/index.html` — frontend UI
-   `test/route.http` — sample HTTP request

## Troubleshooting

-   `Failed to contact OpenAI`: check `OPENAI_API_KEY`, ensure network access, and confirm the model is available to your account (try `gpt-3.5-turbo`). Restart Flask after changing `.env`.
-   Changes in `.env` require restarting the Flask server.

## Next steps

-   Add authentication and rate limiting before production use.
-   Add logging/monitoring for upstream errors.
-   Replace the dev server with a production WSGI server (e.g., gunicorn or waitress) when deploying.
