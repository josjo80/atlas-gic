from dataclasses import dataclass, field
from typing import Dict, List

from .eod_cycle import AgentSignal


@dataclass
class Scorecard:
    sharpe: Dict[str, float] = field(default_factory=dict)
    history: Dict[str, List[float]] = field(default_factory=dict)

    def update(self, signals: List[AgentSignal]) -> None:
        for s in signals:
            self.history.setdefault(s.agent, []).append(s.score)

        # mock sharpe: mean / std
        for agent, vals in self.history.items():
            if len(vals) < 2:
                self.sharpe[agent] = vals[-1]
                continue
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
            std = variance ** 0.5 if variance > 0 else 1.0
            self.sharpe[agent] = round(mean / std, 4)
