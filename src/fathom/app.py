"""Flask application factory for the Fathom web application."""

from __future__ import annotations

from flask import Flask

from fathom.config import Settings


def create_app(settings: Settings | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        settings: Optional Settings instance. If None, a new one is
            created from environment variables and defaults.

    Returns:
        A configured Flask application instance with routes registered.

    """
    if settings is None:
        settings = Settings()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["FATHOM_SETTINGS"] = settings

    from fathom.formatting import comma_format
    from fathom.routes import bp

    app.jinja_env.filters["comma"] = comma_format
    app.register_blueprint(bp)

    return app
