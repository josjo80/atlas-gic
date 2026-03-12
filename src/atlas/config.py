"""Configuration loaded from environment / .env file."""
import os
from dataclasses import dataclass


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv optional; fall back to bare os.environ


_load_dotenv()


@dataclass
class Config:
    finnhub_api_key: str = ""
    massive_api_key: str = ""
    anthropic_api_key: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            finnhub_api_key=os.getenv("FINNHUB_API_KEY", ""),
            massive_api_key=os.getenv("MASSIVE_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        )

    @property
    def has_market_data(self) -> bool:
        return bool(self.finnhub_api_key or self.massive_api_key)

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key)


def get_settings() -> Config:
    """Return a Config populated from environment variables and .env file."""
    return Config.from_env()
