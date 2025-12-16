from app import create_app

app = create_app()

"""
## Next steps

-   Add authentication and rate limiting before production use.
-   Add logging/monitoring for upstream errors.
-   Replace the dev server with a production WSGI server (e.g., gunicorn or waitress) when deploying.

"""
