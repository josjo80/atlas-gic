import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from ..config import Config

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    prices: Dict[str, float]
    returns: Dict[str, float]
    source: str = "mock"


def get_mock_market_data(tickers: List[str]) -> MarketSnapshot:
    """Generate a fake price/return snapshot for a list of tickers."""
    prices = {t: round(random.uniform(20, 500), 2) for t in tickers}
    returns = {t: round(random.uniform(-0.05, 0.05), 4) for t in tickers}
    return MarketSnapshot(prices=prices, returns=returns, source="mock")


def get_market_data(tickers: List[str], config: "Config") -> MarketSnapshot:
    """Return a MarketSnapshot from the best available source.

    Priority: Massive → Finnhub → mock.
    Falls back to mock on any error so the system keeps running.
    """
    if config.massive_api_key:
        try:
            from ..data.providers.massive import fetch_quotes
            quotes = fetch_quotes(tickers, config.massive_api_key)
            prices = {t: v[0] for t, v in quotes.items()}
            returns = {t: v[1] for t, v in quotes.items()}
            return MarketSnapshot(prices=prices, returns=returns, source="massive")
        except Exception as exc:
            logger.warning("Massive fetch failed (%s); falling back", exc)

    if config.finnhub_api_key:
        try:
            from ..data.providers.finnhub import fetch_quotes
            quotes = fetch_quotes(tickers, config.finnhub_api_key)
            prices = {t: v[0] for t, v in quotes.items()}
            returns = {t: v[1] for t, v in quotes.items()}
            return MarketSnapshot(prices=prices, returns=returns, source="finnhub")
        except Exception as exc:
            logger.warning("Finnhub fetch failed (%s); falling back to mock", exc)

    return get_mock_market_data(tickers)
