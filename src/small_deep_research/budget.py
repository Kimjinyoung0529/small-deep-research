from __future__ import annotations

from dataclasses import dataclass, field


class BudgetExceeded(RuntimeError):
    pass


def estimate_tokens(text: str) -> int:
    """Rough, model-agnostic token estimate (~1 token per 3 chars; Korean-safe upper-ish bound)."""
    return max(1, len(text) // 3) if text else 0


@dataclass
class Budget:
    max_steps: int = 3          # search rounds (queries executed)
    max_pages: int = 6          # pages fetched
    max_tokens: int = 20000     # estimated prompt+completion tokens across all LLM calls
    steps: int = 0
    pages: int = 0
    tokens: int = 0
    log: list[str] = field(default_factory=list)

    def can_step(self) -> bool:
        return self.steps < self.max_steps

    def can_fetch(self) -> bool:
        return self.pages < self.max_pages

    def tokens_left(self) -> int:
        return self.max_tokens - self.tokens

    def use_step(self) -> None:
        if not self.can_step():
            raise BudgetExceeded("max_steps")
        self.steps += 1

    def use_page(self) -> None:
        if not self.can_fetch():
            raise BudgetExceeded("max_pages")
        self.pages += 1

    def use_tokens(self, n: int) -> None:
        self.tokens += n
        if self.tokens > self.max_tokens:
            raise BudgetExceeded("max_tokens")

    def summary(self) -> dict:
        return {"steps": f"{self.steps}/{self.max_steps}", "pages": f"{self.pages}/{self.max_pages}",
                "tokens_est": f"{self.tokens}/{self.max_tokens}"}
