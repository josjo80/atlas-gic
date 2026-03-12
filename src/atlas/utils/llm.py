from dataclasses import dataclass


@dataclass
class LLMClient:
    """Placeholder LLM client."""

    provider: str = "mock"

    def generate(self, prompt: str) -> str:
        return f"[mock response] {prompt[:80]}"
