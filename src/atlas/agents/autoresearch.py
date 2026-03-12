"""Autoresearch loop: find worst agent, tweak its prompt via git branch,
evaluate improvement, keep or revert.

Real git flow (requires git repo + write access):
  1. Identify worst agent by rolling Sharpe.
  2. Create branch  autoresearch/{agent}/{timestamp}
  3. Read/create prompt file at  prompts/agents/{agent}.md
  4. Ask LLM to generate a targeted improvement.
  5. Write updated prompt and commit.
  6. Simulate evaluation (N mock days).
  7. Keep branch if Sharpe improved; else checkout main and delete branch.

Falls back to a no-op log message if git operations fail (e.g. detached HEAD,
no commits yet, read-only filesystem).
"""
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from ..config import Config
    from ..utils.llm import LLMClient

logger = logging.getLogger(__name__)

_EVAL_ROUNDS = 5   # mock rounds used to estimate post-change Sharpe
_PROMPTS_DIR = "prompts/agents"


@dataclass
class AutoresearchResult:
    modified_agent: Optional[str]
    branch: Optional[str]
    kept: bool
    pre_sharpe: float = 0.0
    post_sharpe: float = 0.0


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_sharpe(n: int = _EVAL_ROUNDS) -> float:
    """Simulate a short evaluation run and return a Sharpe-like score."""
    vals = [random.gauss(0, 1) for _ in range(n)]
    mean = sum(vals) / len(vals)
    std = (sum((v - mean) ** 2 for v in vals) / (n - 1)) ** 0.5 if n > 1 else 1.0
    return round(mean / std, 4)


def _prompt_path(repo: Path, agent: str) -> Path:
    return repo / _PROMPTS_DIR / f"{agent}.md"


def _read_or_create_prompt(path: Path, agent: str) -> str:
    if path.exists():
        return path.read_text()
    stub = (
        f"# {agent.title()} Agent\n\n"
        f"You are the **{agent}** trading agent in the ATLAS system.\n\n"
        "## Role\nAnalyse relevant market signals and provide a directional conviction score.\n\n"
        "## Output\nA signal score from -100 (strong sell) to 100 (strong buy).\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stub)
    return stub


# ── main entry point ──────────────────────────────────────────────────────────

def run_autoresearch(
    sharpe: Dict[str, float],
    config: "Config | None" = None,
    llm: "LLMClient | None" = None,
) -> AutoresearchResult:
    """Pick worst agent and attempt a real git-backed prompt improvement."""
    if not sharpe:
        return AutoresearchResult(modified_agent=None, branch=None, kept=False)

    worst_agent, worst_sharpe = min(sharpe.items(), key=lambda kv: kv[1])

    try:
        result = _run_real_loop(worst_agent, worst_sharpe, llm)
    except Exception as exc:
        logger.warning("Autoresearch git loop failed (%s); skipping", exc)
        result = AutoresearchResult(
            modified_agent=worst_agent, branch=None, kept=False,
            pre_sharpe=worst_sharpe, post_sharpe=worst_sharpe,
        )
    return result


def _run_real_loop(
    agent: str,
    pre_sharpe: float,
    llm: "LLMClient | None",
) -> AutoresearchResult:
    from ..utils.git_ops import (
        get_repo_root, get_current_branch,
        create_branch, checkout_branch, delete_branch,
        commit_file,
    )

    repo = get_repo_root()
    base_branch = get_current_branch(repo)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    branch_name = f"autoresearch/{agent}/{timestamp}"

    prompt_path = _prompt_path(repo, agent)
    current_prompt = _read_or_create_prompt(prompt_path, agent)

    # Generate improved prompt
    if llm is not None:
        new_prompt = llm.improve_prompt(agent, pre_sharpe, current_prompt)
    else:
        new_prompt = current_prompt + f"\n\n<!-- autoresearch: sharpe={pre_sharpe:.3f} -->"

    # Create branch, write file, commit
    create_branch(branch_name, repo)
    prompt_path.write_text(new_prompt)
    commit_file(
        prompt_path,
        f"autoresearch: improve {agent} prompt (sharpe={pre_sharpe:.3f})",
        repo,
    )
    logger.info("Autoresearch committed to branch %s", branch_name)

    # Evaluate: simulate _EVAL_ROUNDS of mock scoring
    post_sharpe = _mock_sharpe()
    kept = post_sharpe > pre_sharpe

    if not kept:
        checkout_branch(base_branch, repo)
        delete_branch(branch_name, repo)
        logger.info(
            "Autoresearch reverted (pre=%.3f post=%.3f)", pre_sharpe, post_sharpe
        )
    else:
        logger.info(
            "Autoresearch kept branch %s (pre=%.3f post=%.3f)",
            branch_name, pre_sharpe, post_sharpe,
        )

    return AutoresearchResult(
        modified_agent=agent,
        branch=branch_name if kept else None,
        kept=kept,
        pre_sharpe=pre_sharpe,
        post_sharpe=post_sharpe,
    )
