"""
Application configuration via environment variables.

Uses pydantic-settings to provide typed, validated configuration
with FATHOM_-prefixed environment variables and sensible defaults.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application settings loaded from FATHOM_-prefixed env vars.

    All fields have sensible defaults so the app runs with zero configuration.
    Invalid values cause a startup crash with a clear validation error.

    Attributes:
        secret_key: Flask secret key for session signing.
        host: Network interface to bind to.
        port: Port number to listen on.
        debug: Enable Flask debug mode.
        workers: Number of gunicorn worker processes.
        default_return_rate: Default investment return rate for comparisons.
        default_inflation_rate: Default inflation rate (as decimal, e.g. 0.03).
        default_tax_rate: Default tax rate (as decimal, e.g. 0.22).

    """

    model_config = SettingsConfigDict(
        env_prefix="FATHOM_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: str = Field(default_factory=lambda: "fathom-dev-key")
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False
    workers: int = 2
    default_return_rate: float = 0.07
    default_inflation_rate: float = 0.03
    default_tax_rate: float = 0.22
