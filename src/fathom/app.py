"""Flask application factory for the Fathom web application."""

import os

from flask import Flask


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        A configured Flask application instance with routes registered.

    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fathom-dev-key")

    from fathom.routes import bp

    app.register_blueprint(bp)

    return app
