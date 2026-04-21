"""Tests for metrics collection."""

from __future__ import annotations

import time

import pytest

from myagent.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    Timer,
)


class TestCounter:
    def test_initial_value(self):
        c = Counter("test_counter")
        assert c.get() == 0

    def test_increment(self):
        c = Counter("test_counter")
        c.inc()
        assert c.get() == 1

    def test_increment_by_amount(self):
        c = Counter("test_counter")
        c.inc(5)
        assert c.get() == 5

    def test_reset(self):
        c = Counter("test_counter")
        c.inc(10)
        c.reset()
        assert c.get() == 0


class TestGauge:
    def test_initial_value(self):
        g = Gauge("test_gauge")
        assert g.get() == 0

    def test_set(self):
        g = Gauge("test_gauge")
        g.set(42)
        assert g.get() == 42

    def test_inc(self):
        g = Gauge("test_gauge")
        g.set(10)
        g.inc()
        assert g.get() == 11

    def test_dec(self):
        g = Gauge("test_gauge")
        g.set(10)
        g.dec(3)
        assert g.get() == 7


class TestHistogram:
    def test_observe(self):
        h = Histogram("test_hist")
        h.observe(0.05)
        assert h.get_count() == 1
        assert h.get_sum() == 0.05

    def test_buckets(self):
        h = Histogram("test_hist")
        h.observe(0.01)
        h.observe(0.1)
        h.observe(1.0)

        # First bucket (0.005) should have 0
        assert h.buckets[0].count == 0
        # Second bucket (0.01) should have 1
        assert h.buckets[1].count == 1
        # Value 0.1 falls in bucket 0.1 (index 4), not 0.025
        # So bucket 2 (0.025) should have 1 (only 0.01)
        assert h.buckets[2].count == 1
        # Bucket 4 (0.1) should have 2 (0.01 and 0.1)
        assert h.buckets[4].count == 2


class TestTimer:
    def test_timer_context(self):
        h = Histogram("test_timer")
        with Timer(h):
            time.sleep(0.01)

        assert h.get_count() == 1
        assert h.get_sum() >= 0.01


class TestMetricsRegistry:
    def test_counter_creation(self):
        reg = MetricsRegistry()
        c = reg.counter("requests", "Total requests")
        assert isinstance(c, Counter)

    def test_gauge_creation(self):
        reg = MetricsRegistry()
        g = reg.gauge("active_sessions")
        assert isinstance(g, Gauge)

    def test_histogram_creation(self):
        reg = MetricsRegistry()
        h = reg.histogram("latency")
        assert isinstance(h, Histogram)

    def test_get_all_metrics(self):
        reg = MetricsRegistry()
        reg.counter("requests").inc(5)
        reg.gauge("active").set(3)
        reg.histogram("latency").observe(0.1)

        metrics = reg.get_all_metrics()
        assert metrics["counters"]["requests"] == 5
        assert metrics["gauges"]["active"] == 3
        assert metrics["histograms"]["latency"]["count"] == 1

    def test_prometheus_export(self):
        reg = MetricsRegistry()
        reg.counter("requests").inc(5)
        reg.gauge("active").set(3)

        output = reg.export_prometheus()
        assert "requests 5.0" in output
        assert "active 3" in output
        assert "# TYPE requests counter" in output
        assert "# TYPE active gauge" in output
