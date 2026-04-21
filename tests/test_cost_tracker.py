"""Tests for CostTracker."""

from pathlib import Path

import pytest

from myagent.cost.tracker import CostTracker, ModelPricing


class TestModelPricing:
    def test_pricing_creation(self):
        pricing = ModelPricing(
            model="gpt-4o",
            input_price_per_1k=0.005,
            output_price_per_1k=0.015,
        )
        assert pricing.model == "gpt-4o"
        assert pricing.input_price_per_1k == 0.005
        assert pricing.output_price_per_1k == 0.015

    def test_calculate_cost(self):
        pricing = ModelPricing(
            model="gpt-4o",
            input_price_per_1k=0.005,
            output_price_per_1k=0.015,
        )
        cost = pricing.calculate_cost(input_tokens=1000, output_tokens=500)
        assert cost == pytest.approx(0.005 + 0.0075, rel=1e-6)

    def test_calculate_cost_zero(self):
        pricing = ModelPricing(
            model="cheap",
            input_price_per_1k=0.0,
            output_price_per_1k=0.0,
        )
        cost = pricing.calculate_cost(input_tokens=10000, output_tokens=10000)
        assert cost == 0.0


class TestCostTracker:
    def test_tracker_creation(self):
        tracker = CostTracker()
        assert tracker.total_cost == 0.0
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0

    def test_record_usage(self):
        tracker = CostTracker()
        tracker.record_usage(
            provider="openai",
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )

        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
        assert tracker.total_cost > 0

    def test_record_usage_unknown_model(self):
        tracker = CostTracker()
        tracker.record_usage(
            provider="openai",
            model="unknown-model-12345",
            input_tokens=1000,
            output_tokens=500,
        )

        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
        assert tracker.total_cost == 0.0

    def test_multiple_records(self):
        tracker = CostTracker()
        tracker.record_usage("openai", "gpt-4o", 1000, 500)
        tracker.record_usage("anthropic", "claude-sonnet", 2000, 1000)

        assert tracker.total_input_tokens == 3000
        assert tracker.total_output_tokens == 1500
        assert tracker.total_cost > 0

    def test_get_summary(self):
        tracker = CostTracker()
        tracker.record_usage("openai", "gpt-4o", 1000, 500)

        summary = tracker.get_summary()
        assert summary["total_cost_usd"] > 0
        assert summary["total_input_tokens"] == 1000
        assert summary["total_output_tokens"] == 500
        assert summary["total_tokens"] == 1500
        assert "gpt-4o" in summary["models_used"]

    def test_get_breakdown(self):
        tracker = CostTracker()
        tracker.record_usage("openai", "gpt-4o", 1000, 500)
        tracker.record_usage("openai", "gpt-4o", 2000, 1000)

        breakdown = tracker.get_breakdown()
        assert len(breakdown) == 1
        assert breakdown[0]["model"] == "gpt-4o"
        assert breakdown[0]["calls"] == 2
        assert breakdown[0]["input_tokens"] == 3000
        assert breakdown[0]["output_tokens"] == 1500

    def test_reset(self):
        tracker = CostTracker()
        tracker.record_usage("openai", "gpt-4o", 1000, 500)
        tracker.reset()

        assert tracker.total_cost == 0.0
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0

    def test_pricing_registry_has_common_models(self):
        tracker = CostTracker()
        common_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-sonnet-4",
            "claude-opus-4",
            "deepseek-chat",
            "deepseek-reasoner",
        ]
        for model in common_models:
            assert model in tracker._pricing

    def test_budget_warning(self):
        tracker = CostTracker(budget_limit=0.01)
        tracker.record_usage("openai", "gpt-4o", 10000, 5000)

        assert tracker.is_over_budget() is True

    def test_budget_not_exceeded(self):
        tracker = CostTracker(budget_limit=10.0)
        tracker.record_usage("openai", "gpt-4o", 100, 50)

        assert tracker.is_over_budget() is False
