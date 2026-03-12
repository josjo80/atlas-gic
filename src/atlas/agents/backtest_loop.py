from ..config import Config
from ..utils.llm import make_llm_client
from .market_data import get_market_data
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


def run_backtest(days: int, logger, config: Config | None = None) -> None:
    if config is None:
        config = Config.from_env()

    llm = make_llm_client(config)
    scorecard = Scorecard()

    logger.info(
        "Data source: %s | LLM: %s",
        "real" if config.has_market_data else "mock",
        "anthropic" if llm.is_real else "mock",
    )

    for day in range(1, days + 1):
        logger.info("Day %s", day)
        snapshot = get_market_data(DEFAULT_TICKERS, config)
        signals = run_eod_cycle(DEFAULT_AGENTS, snapshot, llm=llm)
        scorecard.update(signals)

        top = sorted(scorecard.sharpe.items(), key=lambda kv: kv[1], reverse=True)[:3]
        logger.info("Top agents: %s | data=%s", top, snapshot.source)

        if day % 5 == 0:
            result = run_autoresearch(scorecard.sharpe, config=config, llm=llm)
            logger.info(
                "Autoresearch agent=%s kept=%s branch=%s pre=%.3f post=%.3f",
                result.modified_agent,
                result.kept,
                result.branch,
                result.pre_sharpe,
                result.post_sharpe,
            )
