from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from .market_data import MarketSnapshot

if TYPE_CHECKING:
    from ..utils.llm import LLMClient


@dataclass
class AgentSignal:
    agent: str
    ticker: str
    score: float


def run_eod_cycle(
    agents: List[str],
    snapshot: MarketSnapshot,
    llm: "LLMClient | None" = None,
) -> List[AgentSignal]:
    """Run the end-of-day agent debate pipeline.

    Each agent is assigned a ticker round-robin and scored.
    If an LLMClient is provided and is backed by a real API, Claude
    generates the signal score; otherwise falls back to return-scaled mock.
    """
    signals: List[AgentSignal] = []
    tickers = list(snapshot.prices.keys())
    for i, agent in enumerate(agents):
        ticker = tickers[i % len(tickers)]
        if llm is not None:
            score = llm.score_agent(agent, ticker, snapshot)
        else:
            score = round(snapshot.returns[ticker] * 100, 3)
        signals.append(AgentSignal(agent=agent, ticker=ticker, score=score))
    return signals
