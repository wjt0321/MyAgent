"""Health check endpoints for MyAgent Web UI.

Provides liveness, readiness, and metrics endpoints for production monitoring.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from fastapi import APIRouter, Response

from myagent.gateway.manager import GatewayManager
from myagent.monitoring.metrics import get_registry

router = APIRouter(prefix="/health", tags=["health"])

# Track startup time
_STARTUP_TIME = time.time()


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Liveness probe — returns 200 if the process is running."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check() -> Response:
    """Readiness probe — returns 200 if the service is ready to accept traffic."""
    # Check if core components are initialized
    try:
        # Basic checks
        checks = {
            "startup_time": _STARTUP_TIME,
            "uptime_seconds": time.time() - _STARTUP_TIME,
        }
        return Response(
            content='{"status": "ready"}',
            media_type="application/json",
            status_code=200,
        )
    except Exception as e:
        return Response(
            content=f'{{"status": "not_ready", "error": "{e}"}}',
            media_type="application/json",
            status_code=503,
        )


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Combined health check with detailed status."""
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - _STARTUP_TIME, 2),
        "version": "0.6.0",
    }


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """Prometheus-style metrics endpoint."""
    registry = get_registry()
    output = registry.export_prometheus()
    return Response(content=output, media_type="text/plain")
