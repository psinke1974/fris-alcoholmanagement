"""Entry point voor development. Gebruik in productie een WSGI-server (zie docs/deployment.md)."""

import os

from app import create_app

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")
    if debug:
        os.environ.setdefault("FLASK_DEBUG", "1")
    app = create_app()
    app.run(debug=debug, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8080")))
