from typing import List

from .market_data import get_mock_market_data
from .eod_cycle import run_eod_cycle
from .scorecard import Scorecard
from .autoresearch import run_autoresearch


DEFAULT_AGENTS = [
    "macro",
    "china",
    "semis",
    "energy",
    "biotech",
    "consumer",
    "financials",
    "cro",
    "cio",
]

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]


def run_backtest(days: int, logger) -> None:
    scorecard = Scorecard()

    for day in range(1, days + 1):
        logger.info("Day %s", day)
        snapshot = get_mock_market_data(DEFAULT_TICKERS)
        signals = run_eod_cycle(DEFAULT_AGENTS, snapshot)
        scorecard.update(signals)

        top = sorted(scorecard.sharpe.items(), key=lambda kv: kv[1], reverse=True)[:3]
        logger.info("Top agents: %s", top)

        if day % 5 == 0:
            result = run_autoresearch(scorecard.sharpe)
            logger.info("Autoresearch modified=%s kept=%s", result.modified_agent, result.kept)
