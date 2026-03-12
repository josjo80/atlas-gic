import random
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class MarketSnapshot:
    prices: Dict[str, float]
    returns: Dict[str, float]


def get_mock_market_data(tickers: List[str]) -> MarketSnapshot:
    """Generate a fake price/return snapshot for a list of tickers."""
    prices = {t: round(random.uniform(20, 500), 2) for t in tickers}
    returns = {t: round(random.uniform(-0.05, 0.05), 4) for t in tickers}
    return MarketSnapshot(prices=prices, returns=returns)
