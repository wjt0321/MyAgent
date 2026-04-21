"""Metrics collection for MyAgent.

Lightweight Prometheus-style metrics for monitoring performance.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class HistogramBucket:
    """A bucket in a histogram."""

    upper_bound: float
    count: int = 0


@dataclass
class MetricValue:
    """A single metric value with timestamp."""

    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


class Counter:
    """A monotonically increasing counter."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self._value = 0.0
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0) -> None:
        """Increment the counter."""
        with self._lock:
            self._value += amount

    def get(self) -> float:
        """Get current value."""
        with self._lock:
            return self._value

    def reset(self) -> None:
        """Reset counter to zero."""
        with self._lock:
            self._value = 0.0


class Gauge:
    """A gauge that can go up and down."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self._value = 0.0
        self._lock = threading.Lock()

    def set(self, value: float) -> None:
        """Set the gauge value."""
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0) -> None:
        """Increment the gauge."""
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrement the gauge."""
        with self._lock:
            self._value -= amount

    def get(self) -> float:
        """Get current value."""
        with self._lock:
            return self._value


class Histogram:
    """A histogram for tracking distributions."""

    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: Optional[List[float]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.buckets = [HistogramBucket(b) for b in (buckets or self.DEFAULT_BUCKETS)]
        self._sum = 0.0
        self._count = 0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        """Observe a value."""
        with self._lock:
            self._sum += value
            self._count += 1
            for bucket in self.buckets:
                if value <= bucket.upper_bound:
                    bucket.count += 1

    def get_sum(self) -> float:
        with self._lock:
            return self._sum

    def get_count(self) -> float:
        with self._lock:
            return float(self._count)


class Timer:
    """Context manager for timing operations."""

    def __init__(self, histogram: Histogram) -> None:
        self.histogram = histogram
        self.start_time: Optional[float] = None

    def __enter__(self) -> "Timer":
        self.start_time = time.time()
        return self

    def __exit__(self, *args: Any) -> None:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.histogram.observe(duration)


class MetricsRegistry:
    """Registry for all metrics."""

    def __init__(self) -> None:
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create a counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description)
            return self._counters[name]

    def gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create a gauge."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description)
            return self._gauges[name]

    def histogram(
        self, name: str, description: str = "", buckets: Optional[List[float]] = None
    ) -> Histogram:
        """Get or create a histogram."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, buckets)
            return self._histograms[name]

    def timer(self, name: str, description: str = "") -> Timer:
        """Create a timer for a histogram."""
        hist = self.histogram(name, description)
        return Timer(hist)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metric values."""
        return {
            "counters": {name: c.get() for name, c in self._counters.items()},
            "gauges": {name: g.get() for name, g in self._gauges.items()},
            "histograms": {
                name: {
                    "count": h.get_count(),
                    "sum": h.get_sum(),
                    "buckets": [
                        {"le": b.upper_bound, "count": b.count} for b in h.buckets
                    ],
                }
                for name, h in self._histograms.items()
            },
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        for name, counter in self._counters.items():
            lines.append(f"# HELP {name} {counter.description or name}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {counter.get()}")

        for name, gauge in self._gauges.items():
            lines.append(f"# HELP {name} {gauge.description or name}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {gauge.get()}")

        for name, hist in self._histograms.items():
            lines.append(f"# HELP {name} {hist.description or name}")
            lines.append(f"# TYPE {name} histogram")
            for bucket in hist.buckets:
                lines.append(f'{name}_bucket{{le="{bucket.upper_bound}"}} {bucket.count}')
            lines.append(f'{name}_bucket{{le="+Inf"}} {int(hist.get_count())}')
            lines.append(f"{name}_sum {hist.get_sum()}")
            lines.append(f"{name}_count {int(hist.get_count())}")

        return "\n".join(lines) + "\n"


# Global registry
REGISTRY = MetricsRegistry()


def get_registry() -> MetricsRegistry:
    """Get the global metrics registry."""
    return REGISTRY
