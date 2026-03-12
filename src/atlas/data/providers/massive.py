"""Massive.com market data adapter.

Uses the Massive REST API v2 Stocks Previous Day Bar endpoint:
  GET https://api.massive.com/v2/aggs/ticker/{ticker}/prev
Auth via `apiKey` query parameter (not Bearer token).
Returns current price and daily percent change for each ticker.
"""
import time
from typing import Dict, List, Tuple

_BASE = "https://api.massive.com"
_DELAY = 12.5  # seconds between requests (5 req/min limit)
_MAX_RETRIES = 2
_BACKOFF_SECONDS = 12.5


def fetch_quotes(tickers: List[str], api_key: str) -> Dict[str, Tuple[float, float]]:
    """Return {ticker: (price, daily_return)} for each ticker.

    Calls GET /v2/aggs/ticker/{ticker}/prev with apiKey as a query param.
    daily_return is fractional (e.g. 0.012 = +1.2%).
    Raises on HTTP/parsing errors so the caller can fall back.
    """
    import requests  # lazy import so mock path has no dependency

    results: Dict[str, Tuple[float, float]] = {}
    for ticker in tickers:
        attempt = 0
        while True:
            resp = requests.get(
                f"{_BASE}/v2/aggs/ticker/{ticker}/prev",
                params={"apiKey": api_key},
                timeout=5,
            )
            if resp.status_code == 429 and attempt < _MAX_RETRIES:
                attempt += 1
                time.sleep(_BACKOFF_SECONDS * attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            bars = data.get("results", [])
            if not bars:
                results[ticker] = (0.0, 0.0)
                break
            bar = bars[0]
            close = float(bar["c"])
            open_ = float(bar["o"])
            daily_return = (close / open_ - 1) if open_ else 0.0
            results[ticker] = (close, round(daily_return, 6))
            break
        time.sleep(_DELAY)
    return results
