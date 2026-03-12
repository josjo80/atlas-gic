"""LLM client with Anthropic backend and mock fallback.

If ANTHROPIC_API_KEY is set the real Claude API is used.
Otherwise all calls return deterministic mock responses so the
system runs without any API credentials.
"""
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import Config
    from ..agents.market_data import MarketSnapshot

logger = logging.getLogger(__name__)

# Models used per task (lightweight scoring vs. heavier reasoning)
_SCORE_MODEL = "claude-haiku-4-5-20251001"
_REASON_MODEL = "claude-sonnet-4-6"

_MAX_TOKENS_SCORE = 16
_MAX_TOKENS_REASON = 1024


class LLMClient:
    """Thin wrapper around Anthropic messages API with mock fallback."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key
        self._client = None
        if api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=api_key)
                logger.debug("LLMClient: using Anthropic backend")
            except ImportError:
                logger.warning(
                    "anthropic package not installed; falling back to mock LLM"
                )

    @property
    def is_real(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, *, model: str = _REASON_MODEL, max_tokens: int = _MAX_TOKENS_REASON) -> str:
        if not self._client:
            return f"[mock] {prompt[:80]}"
        msg = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    def score_agent(self, agent: str, ticker: str, snapshot: "MarketSnapshot") -> float:
        """Return a signal in [-100, 100] for the given agent/ticker/snapshot.

        Uses Haiku for speed/cost. Falls back to return-scaled mock.
        """
        daily_return = snapshot.returns.get(ticker, 0.0)
        if not self._client:
            return round(daily_return * 100, 3)

        price = snapshot.prices.get(ticker, float("nan"))
        prompt = (
            f"You are scoring the '{agent}' trading agent on {ticker}.\n"
            f"Current price: ${price:.2f} | Today's return: {daily_return:+.2%} | "
            f"Data source: {snapshot.source}.\n"
            "Respond with a single integer from -100 to 100 representing "
            "this agent's signal strength (100 = very strong buy, -100 = very strong sell)."
        )
        try:
            raw = self.generate(prompt, model=_SCORE_MODEL, max_tokens=_MAX_TOKENS_SCORE)
            match = re.search(r"-?\d+", raw)
            if match:
                return float(max(-100, min(100, int(match.group()))))
        except Exception as exc:
            logger.warning("LLM score_agent failed (%s); using mock score", exc)
        return round(daily_return * 100, 3)

    def improve_prompt(self, agent: str, sharpe: float, current_prompt: str) -> str:
        """Ask Claude to suggest a prompt improvement for the worst agent.

        Returns the full updated prompt text. Falls back to appending a mock note.
        """
        if not self._client:
            return current_prompt + f"\n\n<!-- autoresearch mock tweak: sharpe was {sharpe:.3f} -->"

        prompt = (
            f"You are improving the prompt for the '{agent}' trading agent in a multi-agent finance system.\n"
            f"This agent's recent Sharpe ratio is {sharpe:.3f} (lowest performing).\n\n"
            "Current prompt:\n"
            "---\n"
            f"{current_prompt}\n"
            "---\n\n"
            "Suggest ONE specific, concrete modification to improve this agent's analytical focus "
            "and signal quality. Keep changes minimal and targeted. "
            "Respond with the complete updated prompt text only — no explanation."
        )
        try:
            return self.generate(prompt, model=_REASON_MODEL, max_tokens=_MAX_TOKENS_REASON)
        except Exception as exc:
            logger.warning("LLM improve_prompt failed (%s); using mock tweak", exc)
            return current_prompt + f"\n\n<!-- autoresearch mock tweak: sharpe was {sharpe:.3f} -->"


def make_llm_client(config: "Config") -> LLMClient:
    return LLMClient(api_key=config.anthropic_api_key)
