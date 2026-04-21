"""Cost tracker for MyAgent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelPricing:
    """Pricing information for an LLM model."""

    model: str
    input_price_per_1k: float
    output_price_per_1k: float

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for given token usage."""
        input_cost = (input_tokens / 1000) * self.input_price_per_1k
        output_cost = (output_tokens / 1000) * self.output_price_per_1k
        return input_cost + output_cost


DEFAULT_PRICING: dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing("gpt-4o", 0.005, 0.015),
    "gpt-4o-mini": ModelPricing("gpt-4o-mini", 0.00015, 0.0006),
    "gpt-4-turbo": ModelPricing("gpt-4-turbo", 0.01, 0.03),
    "gpt-4": ModelPricing("gpt-4", 0.03, 0.06),
    "claude-sonnet-4": ModelPricing("claude-sonnet-4", 0.003, 0.015),
    "claude-opus-4": ModelPricing("claude-opus-4", 0.015, 0.075),
    "claude-haiku-4": ModelPricing("claude-haiku-4", 0.00025, 0.00125),
    "deepseek-chat": ModelPricing("deepseek-chat", 0.00014, 0.00028),
    "deepseek-reasoner": ModelPricing("deepseek-reasoner", 0.00055, 0.00219),
    "glm-4": ModelPricing("glm-4", 0.001, 0.001),
    "glm-4-plus": ModelPricing("glm-4-plus", 0.002, 0.002),
    "glm-4-flash": ModelPricing("glm-4-flash", 0.0001, 0.0001),
    "moonshot-v1-8k": ModelPricing("moonshot-v1-8k", 0.001, 0.001),
    "moonshot-v1-32k": ModelPricing("moonshot-v1-32k", 0.002, 0.002),
    "moonshot-v1-128k": ModelPricing("moonshot-v1-128k", 0.004, 0.004),
    "abab6.5s-chat": ModelPricing("abab6.5s-chat", 0.001, 0.001),
    "abab6.5-chat": ModelPricing("abab6.5-chat", 0.002, 0.002),
}


@dataclass
class UsageRecord:
    """A single usage record."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float


class CostTracker:
    """Tracks LLM usage costs across providers and models."""

    def __init__(self, budget_limit: float | None = None) -> None:
        self._pricing: dict[str, ModelPricing] = dict(DEFAULT_PRICING)
        self._records: list[UsageRecord] = []
        self.budget_limit = budget_limit
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def register_pricing(self, model: str, input_price: float, output_price: float) -> None:
        """Register pricing for a model."""
        self._pricing[model] = ModelPricing(model, input_price, output_price)

    def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Record token usage and calculate cost."""
        pricing = self._pricing.get(model)
        cost = pricing.calculate_cost(input_tokens, output_tokens) if pricing else 0.0

        record = UsageRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )
        self._records.append(record)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        return cost

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all usage."""
        models = list(dict.fromkeys(r.model for r in self._records))
        return {
            "total_cost_usd": round(self.total_cost, 6),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "models_used": models,
            "budget_limit": self.budget_limit,
            "over_budget": self.is_over_budget(),
        }

    def get_breakdown(self) -> list[dict[str, Any]]:
        """Get per-model cost breakdown."""
        from collections import defaultdict

        stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        )

        for record in self._records:
            s = stats[record.model]
            s["calls"] += 1
            s["input_tokens"] += record.input_tokens
            s["output_tokens"] += record.output_tokens
            s["cost"] += record.cost

        return [
            {
                "model": model,
                "calls": data["calls"],
                "input_tokens": data["input_tokens"],
                "output_tokens": data["output_tokens"],
                "cost_usd": round(data["cost"], 6),
            }
            for model, data in sorted(stats.items())
        ]

    def is_over_budget(self) -> bool:
        """Check if usage has exceeded the budget limit."""
        if self.budget_limit is None:
            return False
        return self.total_cost > self.budget_limit

    def reset(self) -> None:
        """Reset all tracked usage."""
        self._records = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
