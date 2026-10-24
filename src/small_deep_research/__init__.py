"""small-deep-research: a minimal deep research loop for small local models."""
from .budget import Budget, BudgetExceeded
from .engine import ResearchEngine, ResearchResult

__all__ = ["Budget", "BudgetExceeded", "ResearchEngine", "ResearchResult"]
__version__ = "0.0.1"
