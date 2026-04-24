# Phase 8: 生产优化 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 提升 MyAgent 的生产环境可用性，包括监控埋点、LLM 重试、配置热重载、结构化日志

**Architecture:** 在现有 `monitoring/metrics.py`、`config/hot_reload.py`、`logging_config.py` 基础上，补齐与 QueryEngine、LLM Provider、Web Server 的集成

**Tech Stack:** Python 3.12, FastAPI, Prometheus-style metrics, JSON logging, asyncio exponential backoff

---

## Task 1: QueryEngine 监控埋点

**Files:**
- Modify: `src/myagent/engine/query_engine.py`
- Modify: `src/myagent/monitoring/metrics.py` (如有需要)

**Step 1: 在 QueryEngine 中集成 MetricsRegistry**

在 `query_engine.py` 的 `__init__` 和 `_run_loop` 中添加埋点：

```python
from myagent.monitoring.metrics import get_registry

# In __init__:
self._metrics = get_registry()
self._llm_latency_hist = self._metrics.histogram("llm_request_duration_seconds", "LLM request latency")
self._tool_latency_hist = self._metrics.histogram("tool_execution_duration_seconds", "Tool execution latency")
self._turn_counter = self._metrics.counter("query_turns_total", "Total query turns")
self._tool_counter = self._metrics.counter("tool_executions_total", "Total tool executions")
self._error_counter = self._metrics.counter("query_errors_total", "Total query errors")
```

**Step 2: 在 _run_loop 中添加埋点**

- LLM 调用前后计时（latency）
- 工具调用前后计时（latency + success/error）
- 每轮 turn 计数
- 错误计数

**Step 3: 验证 /metrics 端点输出**

Run: `curl http://localhost:8000/health/metrics`
Expected: 包含 `llm_request_duration_seconds`、`tool_execution_duration_seconds` 等指标

**Step 4: Commit**

```bash
git add src/myagent/engine/query_engine.py
git commit -m "feat: QueryEngine添加Prometheus监控埋点"
```

---

## Task 2: LLM Provider 指数退避重试

**Files:**
- Create: `src/myagent/llm/retry.py`
- Modify: `src/myagent/llm/providers/openai.py`
- Modify: `src/myagent/llm/providers/anthropic.py`

**Step 1: 创建重试装饰器**

```python
"""Retry utilities for LLM providers with exponential backoff."""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator for retrying async functions with exponential backoff."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt >= max_retries:
                        logger.error(
                            "Function %s failed after %d retries: %s",
                            func.__name__,
                            max_retries,
                            e,
                        )
                        raise

                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        "Function %s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        func.__name__,
                        attempt + 1,
                        max_retries + 1,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)

            if last_exception:
                raise last_exception
            return None  # type: ignore[return-value]

        return wrapper  # type: ignore[return-value]

    return decorator
```

**Step 2: 在 OpenAIProvider 中应用重试**

在 `stream_messages` 和 `complete` 方法上添加装饰器：

```python
from myagent.llm.retry import retry_with_backoff

class OpenAIProvider(BaseProvider):
    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        retryable_exceptions=(
            asyncio.TimeoutError,
            ConnectionError,
            httpx.HTTPStatusError,
        ),
    )
    async def stream_messages(self, messages, tools=None):
        ...
```

**Step 3: 在 AnthropicProvider 中同样应用**

**Step 4: Commit**

```bash
git add src/myagent/llm/retry.py src/myagent/llm/providers/openai.py src/myagent/llm/providers/anthropic.py
git commit -m "feat: LLMProvider添加指数退避重试机制"
```

---

## Task 3: 配置热重载集成到 Web Server

**Files:**
- Modify: `src/myagent/web/server.py`
- Modify: `src/myagent/config/hot_reload.py`

**Step 1: 在 server.py lifespan 中启动 ConfigWatcher**

```python
from myagent.config.hot_reload import get_watcher

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.session_store = SessionStore()
    app.state.engine_manager = WebEngineManager()
    app.state.task_engine = TaskEngine(app.state.engine_manager)
    app.state.team_orchestrator = TeamOrchestrator(app.state.task_engine)
    
    # Start config hot-reload watcher
    watcher = get_watcher()
    config_path = Path.home() / ".myagent" / "config.yaml"
    if config_path.exists():
        def reload_config():
            logger.info("Config hot-reload triggered")
            # Reload settings
            new_settings = Settings.load()
            app.state.settings = new_settings
        
        watcher.watch(config_path, reload_config)
        watcher.start()
    
    yield
    
    watcher.stop()
```

**Step 2: 添加热重载状态 API**

```python
@app.get("/api/config/status")
async def config_status() -> dict[str, Any]:
    """Get configuration hot-reload status."""
    watcher = get_watcher()
    return {
        "hot_reload_enabled": watcher._running,
        "watched_files": [str(p) for p in watcher._watched_files],
    }
```

**Step 3: Commit**

```bash
git add src/myagent/web/server.py src/myagent/config/hot_reload.py
git commit -m "feat: WebServer集成配置热重载"
```

---

## Task 4: 结构化 JSON 日志集成

**Files:**
- Modify: `src/myagent/cli.py`
- Modify: `src/myagent/web/server.py`
- Modify: `src/myagent/logging_config.py`

**Step 1: CLI 添加 --json-log 参数**

```python
@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    json_log: bool = typer.Option(False, "--json-log", help="Enable JSON structured logging"),
    log_level: str = typer.Option("INFO", "--log-level", help="Log level"),
) -> None:
    _load_env()
    from myagent.logging_config import setup_logging
    
    log_file = Path.home() / ".myagent" / "logs" / "myagent.log"
    setup_logging(
        level=log_level,
        log_file=log_file,
        json_format=json_log,
    )
    
    import uvicorn
    from myagent.web.server import create_app
    ...
```

**Step 2: 在 server.py 中添加请求追踪 ID**

```python
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    logger = logging.getLogger("myagent.web")
    logger.info(
        "Request %s %s",
        request.method,
        request.url.path,
        extra={"request_id": request_id, "method": request.method, "path": request.url.path},
    )
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**Step 3: Commit**

```bash
git add src/myagent/cli.py src/myagent/web/server.py src/myagent/logging_config.py
git commit -m "feat: 添加结构化JSON日志和请求追踪ID"
```

---

## Task 5: 更新文档

**Files:**
- Modify: `docs/reference/03-production.md`
- Modify: `docs/plans/next-iteration.md`

**Step 1: 更新生产部署文档**

添加监控、日志、热重载的使用说明。

**Step 2: 更新 next-iteration.md**

Phase 8 完成度 30% → 80%。

**Step 3: Commit**

```bash
git add docs/
git commit -m "docs: 更新生产优化文档"
```

---

## Task 6: 最终提交到远程

```bash
git push origin master
```

---

*文档版本: v1.0 | 创建时间: 2026-04-24*
