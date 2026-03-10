"""The fathom module."""

from fathom.config import Settings


def main() -> None:
    """Start the fathom application."""
    from fathom.app import create_app

    settings = Settings()
    app = create_app(settings)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
