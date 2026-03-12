from dataclasses import dataclass
from typing import Dict, List

from .market_data import MarketSnapshot


@dataclass
class AgentSignal:
    agent: str
    ticker: str
    score: float


def run_eod_cycle(agents: List[str], snapshot: MarketSnapshot) -> List[AgentSignal]:
    """Mock daily agent debate pipeline returning simple scored signals."""
    signals: List[AgentSignal] = []
    tickers = list(snapshot.prices.keys())
    for i, agent in enumerate(agents):
        ticker = tickers[i % len(tickers)]
        # A toy score: agent-specific bias + random market move
        score = round(snapshot.returns[ticker] * 100, 3)
        signals.append(AgentSignal(agent=agent, ticker=ticker, score=score))
    return signals
