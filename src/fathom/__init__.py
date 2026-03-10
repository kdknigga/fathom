"""The fathom module."""


def main() -> None:
    """Start the fathom application."""
    from fathom.app import create_app

    app = create_app()
    app.run(debug=True)
