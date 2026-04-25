"""Setup readiness detection for MyAgent."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SetupIssue(BaseModel):
    """A single setup issue with a suggested fix."""

    code: str
    level: str
    summary: str
    fix: str


class SetupStatus(BaseModel):
    """Aggregated setup readiness for CLI, TUI, and Web."""

    home: str
    workspace_ready: bool
    config_ready: bool
    env_ready: bool
    llm_ready: bool
    gateway_ready: bool
    overall_ready: bool
    next_action: str
    issues: list[SetupIssue] = Field(default_factory=list)


def get_myagent_home() -> Path:
    """Return the configured MyAgent home directory."""
    home = os.getenv("MYAGENT_HOME")
    if home:
        return Path(home)
    return Path.home() / ".myagent"


def _required_workspace_paths(home: Path) -> list[Path]:
    return [
        home / "workspace",
        home / "memory",
        home / "projects",
        home / "sessions",
        home / "logs",
    ]


def _has_llm_key() -> bool:
    candidates = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "GEMINI_API_KEY",
        "ZHIPU_API_KEY",
        "OPENROUTER_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "DASHSCOPE_API_KEY",
        "DASHSCOPE_CN_API_KEY",
        "MYAGENT_API_KEY",
    ]
    return any(bool(os.getenv(name)) for name in candidates)


def _load_yaml_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return False
    return True


def _next_action(workspace_ready: bool, config_ready: bool, llm_ready: bool) -> str:
    if not workspace_ready or not config_ready:
        return "myagent init --quick"
    if not llm_ready:
        return "myagent init"
    return "myagent --tui"


def get_setup_status(home: Path | None = None) -> SetupStatus:
    """Build a unified setup readiness snapshot."""
    home_dir = home or get_myagent_home()
    config_path = home_dir / "config.yaml"
    env_path = home_dir / ".env"
    gateway_path = home_dir / "gateway.yaml"

    workspace_ready = all(path.exists() for path in _required_workspace_paths(home_dir))
    config_ready = _load_yaml_ok(config_path)
    env_ready = env_path.exists()
    llm_ready = _has_llm_key()
    gateway_ready = _load_yaml_ok(gateway_path) if gateway_path.exists() else False

    issues: list[SetupIssue] = []
    if not workspace_ready:
        issues.append(
            SetupIssue(
                code="workspace_missing",
                level="error",
                summary="Workspace 尚未初始化。",
                fix="运行 `myagent init --quick` 创建基础目录和默认配置。",
            )
        )
    if not config_ready:
        issues.append(
            SetupIssue(
                code="config_missing",
                level="error",
                summary="config.yaml 缺失或格式无效。",
                fix="运行 `myagent init --quick` 重新生成配置文件。",
            )
        )
    if not env_ready:
        issues.append(
            SetupIssue(
                code="env_missing",
                level="warning",
                summary=".env 尚未创建。",
                fix="运行 `myagent init --quick` 生成环境模板，再填入 API Key。",
            )
        )
    if not llm_ready:
        issues.append(
            SetupIssue(
                code="llm_missing",
                level="error",
                summary="未检测到可用的 LLM API Key。",
                fix="运行 `myagent init` 配置 provider，或手动编辑 `~/.myagent/.env`。",
            )
        )

    overall_ready = workspace_ready and config_ready and llm_ready
    return SetupStatus(
        home=str(home_dir),
        workspace_ready=workspace_ready,
        config_ready=config_ready,
        env_ready=env_ready,
        llm_ready=llm_ready,
        gateway_ready=gateway_ready,
        overall_ready=overall_ready,
        next_action=_next_action(workspace_ready, config_ready, llm_ready),
        issues=issues,
    )
