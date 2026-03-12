"""Finnhub market data adapter.

Uses the /quote endpoint (free tier, 60 req/min).
Returns current price and daily percent change for each ticker.
"""
import time
from typing import Dict, List, Tuple

_BASE = "https://finnhub.io/api/v1"
_DELAY = 0.1  # seconds between requests — well within free-tier limits


def fetch_quotes(tickers: List[str], api_key: str) -> Dict[str, Tuple[float, float]]:
    """Return {ticker: (price, daily_return)} for each ticker.

    daily_return is fractional (e.g. 0.012 = +1.2%).
    Raises on HTTP errors so the caller can fall back.
    """
    import requests  # lazy import so mock path has no dependency

    results: Dict[str, Tuple[float, float]] = {}
    for ticker in tickers:
        resp = requests.get(
            f"{_BASE}/quote",
            params={"symbol": ticker, "token": api_key},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        price = float(data["c"])        # current price
        pct = float(data.get("dp", 0))  # daily % change
        results[ticker] = (price, round(pct / 100, 6))
        time.sleep(_DELAY)
    return results
