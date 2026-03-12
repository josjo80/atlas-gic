from dataclasses import dataclass
from typing import Dict, Optional

from ..utils.git_ops import mock_commit, mock_revert


@dataclass
class AutoresearchResult:
    modified_agent: Optional[str]
    kept: bool


def run_autoresearch(sharpe: Dict[str, float]) -> AutoresearchResult:
    """Pick worst agent and simulate a prompt tweak decision."""
    if not sharpe:
        return AutoresearchResult(modified_agent=None, kept=False)

    worst = min(sharpe.items(), key=lambda kv: kv[1])[0]
    mock_commit(f"autoresearch: tweak {worst}")

    # In the real system we'd evaluate over multiple days.
    # Here we just keep it 50/50.
    kept = True
    if not kept:
        mock_revert()
    return AutoresearchResult(modified_agent=worst, kept=kept)
