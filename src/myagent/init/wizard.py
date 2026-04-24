"""Interactive initialization wizard for MyAgent.

Guides users through first-time setup: workspace, config, LLM provider, Gateway platforms.
Inspired by OpenClaw's `onboard` and Hermes Agent's setup flow.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from myagent import __version__
from myagent.gateway.base import Platform
from myagent.tui.logo import get_logo
from myagent.workspace.manager import WorkspaceManager, ensure_workspace
from myagent.workspace.templates import initialize_workspace

console = Console()


def _myagent_home() -> Path:
    home = os.getenv("MYAGENT_HOME")
    if home:
        return Path(home)
    return Path.home() / ".myagent"


def _config_path() -> Path:
    return _myagent_home() / "config.yaml"


def _gateway_config_path() -> Path:
    return _myagent_home() / "gateway.yaml"


def _env_path() -> Path:
    return _myagent_home() / ".env"


# ---------------------------------------------------------------------------
# Wizard steps
# ---------------------------------------------------------------------------

def _print_header() -> None:
    term_width = min(console.width, 80)
    logo = get_logo(term_width)
    console.print(f"[dim]{logo}[/dim]")
    console.print(Panel.fit(
        f"[bold cyan]MyAgent v{__version__}[/bold cyan] — 初始化向导\n"
        "[dim]本向导将引导您完成首次配置。[/dim]",
        border_style="cyan",
    ))


def _step_welcome() -> bool:
    console.print("\n[bold]欢迎使用！[/bold] 让我们开始配置 MyAgent。\n")
    console.print("本向导将帮助您完成以下设置：")
    console.print("  1. 创建工作区（soul、memory、projects）")
    console.print("  2. 设置用户画像，获得个性化回复")
    console.print("  3. 配置大语言模型（OpenAI、Anthropic、DeepSeek 等）")
    console.print("  4. 配置消息网关（飞书、Slack、Discord 等）")
    console.print("  5. 生成配置文件和环境变量\n")
    return Confirm.ask("是否继续配置？", default=True)


def _step_workspace() -> Path:
    home = _myagent_home()
    console.print("\n[bold]步骤 1：工作区设置[/bold]")
    console.print(
        "MyAgent 使用工作区来存储记忆、项目和配置。\n"
        "灵感来源于 Claude Code 的 memdir 和 OpenHarness 的 ohmo 系统。\n"
    )

    ws = ensure_workspace(home)
    initialize_workspace(home)

    console.print(f"[green]已创建工作区[/green] {ws}")
    console.print("  [dim]- soul.md（Agent 人格与原则）[/dim]")
    console.print("  [dim]- user.md（您的画像 — 可随时编辑）[/dim]")
    console.print("  [dim]- identity.md（Agent 身份与能力）[/dim]")
    console.print("  [dim]- memory/（持久化记忆存储）[/dim]")
    console.print("  [dim]- projects/（项目工作区）[/dim]")
    console.print("  [dim]- sessions/（对话历史）[/dim]")
    console.print("  [dim]- logs/（操作日志）[/dim]")
    return ws


def _step_user_profile(ws: Path) -> dict[str, str]:
    console.print("\n[bold]步骤 2：用户画像[/bold]")
    console.print(
        "这将帮助我为您提供更个性化的回复。您可以跳过此步骤，稍后编辑 ~/.myagent/user.md。\n"
    )

    profile: dict[str, str] = {}

    if not Confirm.ask("是否立即设置用户画像？", default=True):
        return profile

    name = Prompt.ask("您的姓名（或昵称）", default="用户")
    role = Prompt.ask("您的职位", default="软件工程师")
    tz = Prompt.ask("时区", default="UTC+8")
    langs = Prompt.ask("常用语言", default="中文、英文")

    console.print("\n[bold]技术背景[/bold]")
    primary_langs = Prompt.ask("主要编程语言", default="Python、TypeScript")
    frameworks = Prompt.ask("常用框架和工具", default="FastAPI、React、Docker")
    exp = Prompt.ask("经验水平", choices=["初级", "中级", "高级", "专家"], default="高级")

    console.print("\n[bold]偏好设置[/bold]")
    comm_style = Prompt.ask("沟通风格", choices=["简洁", "详细", "技术"], default="简洁")
    decision = Prompt.ask("决策风格", choices=["快速", " thorough"], default="thorough")

    profile = {
        "name": name,
        "role": role,
        "timezone": tz,
        "languages": langs,
        "primary_langs": primary_langs,
        "frameworks": frameworks,
        "experience": exp,
        "comm_style": comm_style,
        "decision": decision,
    }

    # Write user.md
    user_md = f"""# user.md — 关于您

## 基本信息

- **姓名**: {name}
- **职位**: {role}
- **时区**: {tz}
- **语言**: {langs}

## 技术背景

- **主要语言**: {primary_langs}
- **框架与工具**: {frameworks}
- **经验水平**: {exp}

## 偏好设置

- **沟通风格**: {comm_style}
- **决策风格**: {decision}
- **代码风格**: (例如：PEP 8、Google Style)

## 当前上下文

- **进行中的项目**: (您正在做什么)
- **目标**: (您想要达成什么)
- **挑战**: (当前的阻碍或困难)

## 有效做法

- (您喜欢我帮助您的方式)

## 需要避免

- (让您感到困扰或无效的做法)

---

*本文件帮助我更好地了解您。当您的偏好发生变化时，请随时更新。*
"""
    user_path = ws / "user.md"
    user_path.write_text(user_md, encoding="utf-8")
    console.print(f"[green]已写入[/green] {user_path}")

    # Also create a memory entry for user role
    from myagent.memory.manager import MemoryManager, MemoryEntry, MemoryType
    mm = MemoryManager(ws / "memory")
    entry = MemoryEntry(
        name="用户画像",
        description=f"{name} — {role} ({exp})",
        type=MemoryType.USER,
        content=f"姓名: {name}\n职位: {role}\n经验: {exp}\n语言: {primary_langs}\n框架: {frameworks}\n沟通风格: {comm_style}\n决策风格: {decision}",
    )
    mm.save_memory(entry)
    console.print(f"[green]已保存记忆[/green] 用户画像")

    return profile


def _step_llm_provider() -> dict[str, Any]:
    console.print("\n[bold]步骤 3：大语言模型配置[/bold]")
    console.print("MyAgent 需要一个大语言模型来驱动对话。\n")

    providers = {
        "1": ("openai", "OpenAI（GPT-4o、GPT-4o-mini）"),
        "2": ("anthropic", "Anthropic（Claude 3.5/4 Sonnet、Opus）"),
        "3": ("deepseek", "DeepSeek（V3、R1）"),
        "4": ("gemini", "Google Gemini（1.5 Pro、Flash）"),
        "5": ("qwen", "阿里云通义千问（Qwen-Max、Plus）"),
        "6": ("siliconflow", "SiliconFlow（聚合国内模型）"),
        "7": ("ollama", "Ollama（本地模型 — llama3、mistral 等）"),
        "8": ("azure", "Azure OpenAI 服务"),
        "9": ("openrouter", "OpenRouter（统一 API，支持多模型）"),
        "0": ("skip", "跳过 — 稍后配置"),
    }

    for key, (_, label) in providers.items():
        console.print(f"  [{key}] {label}")

    choice = Prompt.ask(
        "\n请选择提供商",
        choices=list(providers.keys()),
        default="2",
    )

    provider_id, _ = providers[choice]

    if provider_id == "skip":
        console.print("[yellow]已跳过 LLM 配置。稍后请设置 MYAGENT_* 环境变量。[/yellow]")
        return {}

    api_key = Prompt.ask(f"请输入您的 {provider_id.upper()} API 密钥", password=True)

    model_map = {
        "openai": "gpt-4o",
        "anthropic": "claude-sonnet-4-20250514",
        "deepseek": "deepseek-chat",
        "gemini": "gemini-1.5-pro",
        "qwen": "qwen-max",
        "siliconflow": "deepseek-ai/DeepSeek-V3",
        "ollama": "llama3.2",
        "azure": "gpt-4o",
        "openrouter": "anthropic/claude-sonnet-4",
    }
    default_model = model_map.get(provider_id, "")
    model = Prompt.ask("默认模型", default=default_model)

    result: dict[str, Any] = {
        "provider": provider_id,
        "api_key": api_key,
        "model": model,
    }

    if provider_id == "ollama":
        base_url = Prompt.ask("Ollama 服务地址", default="http://localhost:11434")
        result["base_url"] = base_url

    if provider_id == "azure":
        azure_endpoint = Prompt.ask("Azure 终结点 URL")
        result["azure_endpoint"] = azure_endpoint
        result["api_version"] = Prompt.ask("API 版本", default="2024-08-01-preview")

    console.print(f"[green]已配置[/green] {provider_id} -> {model}")
    return result


def _step_gateway_platforms() -> dict[str, Any]:
    console.print("\n[bold]步骤 4：消息网关平台[/bold]")
    console.print(
        "MyAgent 可以接收来自消息平台的指令。\n"
        "启用您想要连接的平台（稍后可以继续添加）。\n"
    )

    platforms: dict[str, Any] = {}

    if Confirm.ask("是否启用 [bold]飞书/Lark[/bold]？", default=False):
        app_id = Prompt.ask("  飞书 App ID")
        app_secret = Prompt.ask("  飞书 App Secret", password=True)
        platforms["feishu"] = {
            "enabled": True,
            "app_id": app_id,
            "app_secret": app_secret,
        }
        console.print("  [green]飞书已配置[/green]")

    if Confirm.ask("是否启用 [bold]Slack[/bold]？", default=False):
        token = Prompt.ask("  Slack Bot Token（xoxb-...）", password=True)
        platforms["slack"] = {
            "enabled": True,
            "token": token,
        }
        console.print("  [green]Slack 已配置[/green]")

    if Confirm.ask("是否启用 [bold]Discord[/bold]？", default=False):
        token = Prompt.ask("  Discord Bot Token", password=True)
        platforms["discord"] = {
            "enabled": True,
            "token": token,
        }
        console.print("  [green]Discord 已配置[/green]")

    if Confirm.ask("是否启用 [bold]Telegram[/bold]？", default=False):
        token = Prompt.ask("  Telegram Bot Token", password=True)
        platforms["telegram"] = {
            "enabled": True,
            "token": token,
        }
        console.print("  [green]Telegram 已配置[/green]")

    if Confirm.ask("是否启用 [bold]钉钉[/bold]？", default=False):
        client_id = Prompt.ask("  钉钉 Client ID")
        client_secret = Prompt.ask("  钉钉 Client Secret", password=True)
        platforms["dingtalk"] = {
            "enabled": True,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        console.print("  [green]钉钉已配置[/green]")

    if not platforms:
        console.print("[yellow]未启用任何平台。网关将以仅 Webhook 模式启动。[/yellow]")

    return platforms


def _step_gateway_settings() -> dict[str, Any]:
    console.print("\n[bold]步骤 5：网关设置[/bold]")

    webhook_secret = secrets.token_urlsafe(32)
    console.print(f"已生成 Webhook 密钥：[dim]{webhook_secret[:8]}...[/dim]")

    session_reset = Prompt.ask(
        "会话重置模式",
        choices=["daily", "idle", "both", "none"],
        default="both",
    )

    return {
        "webhook_secret": webhook_secret,
        "session_reset_mode": session_reset,
    }


def _write_config(
    llm_config: dict[str, Any],
    platforms: dict[str, Any],
    gateway_settings: dict[str, Any],
) -> None:
    home = _myagent_home()

    # Write .env file
    env_lines = ["# MyAgent 环境配置", f"# 由 myagent init v{__version__} 生成"]

    if llm_config.get("provider") and llm_config.get("api_key"):
        provider = llm_config["provider"]
        env_lines.append(f"\n# LLM: {provider}")
        env_lines.append(f"{provider.upper()}_API_KEY={llm_config['api_key']}")
        if provider == "openai":
            env_lines.append(f"OPENAI_MODEL={llm_config.get('model', 'gpt-4o')}")
        elif provider == "anthropic":
            env_lines.append(f"ANTHROPIC_MODEL={llm_config.get('model', 'claude-sonnet-4-20250514')}")
        elif provider == "ollama":
            env_lines.append(f"OLLAMA_BASE_URL={llm_config.get('base_url', 'http://localhost:11434')}")
            env_lines.append(f"OLLAMA_MODEL={llm_config.get('model', 'llama3.2')}")
        elif provider == "azure":
            env_lines.append(f"AZURE_OPENAI_ENDPOINT={llm_config.get('azure_endpoint', '')}")
            env_lines.append(f"AZURE_OPENAI_API_VERSION={llm_config.get('api_version', '2024-08-01-preview')}")
            env_lines.append(f"AZURE_OPENAI_MODEL={llm_config.get('model', 'gpt-4o')}")
        else:
            env_lines.append(f"MYAGENT_MODEL_DEFAULT={llm_config.get('model', '')}")

    for name, cfg in platforms.items():
        env_lines.append(f"\n# Gateway: {name}")
        if name == "feishu":
            env_lines.append(f"FEISHU_APP_ID={cfg['app_id']}")
            env_lines.append(f"FEISHU_APP_SECRET={cfg['app_secret']}")
        elif name == "slack":
            env_lines.append(f"SLACK_BOT_TOKEN={cfg['token']}")
        elif name == "discord":
            env_lines.append(f"DISCORD_BOT_TOKEN={cfg['token']}")
        elif name == "telegram":
            env_lines.append(f"TELEGRAM_BOT_TOKEN={cfg['token']}")
        elif name == "dingtalk":
            env_lines.append(f"DINGTALK_CLIENT_ID={cfg['client_id']}")
            env_lines.append(f"DINGTALK_CLIENT_SECRET={cfg['client_secret']}")

    env_lines.append(f"\n# Gateway 设置")
    env_lines.append(f"WEBHOOK_SECRET={gateway_settings['webhook_secret']}")

    env_file = _env_path()
    env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    console.print(f"[green]已写入[/green] {env_file}")

    # Write gateway.yaml
    gateway_yaml: dict[str, Any] = {
        "platforms": {},
        "default_reset_policy": {
            "mode": gateway_settings["session_reset_mode"],
            "at_hour": 4,
            "idle_minutes": 1440,
            "notify": True,
        },
        "reset_triggers": ["/new", "/reset"],
        "sessions_dir": str(home / "sessions"),
        "always_log_local": True,
        "streaming": {
            "enabled": True,
            "transport": "edit",
            "edit_interval": 1.0,
            "buffer_threshold": 40,
        },
    }

    for name, cfg in platforms.items():
        gateway_yaml["platforms"][name] = {
            "enabled": True,
            "extra": {},
        }
        if name == "feishu":
            gateway_yaml["platforms"][name]["extra"] = {
                "app_id": cfg["app_id"],
                "app_secret": cfg["app_secret"],
                "domain": "feishu",
                "connection_mode": "websocket",
                "auth_mode": "tenant",
            }
        elif name in ("slack", "discord", "telegram"):
            gateway_yaml["platforms"][name]["token"] = cfg["token"]
        elif name == "dingtalk":
            gateway_yaml["platforms"][name]["extra"] = {
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
            }

    gateway_file = _gateway_config_path()
    import yaml
    gateway_file.write_text(yaml.safe_dump(gateway_yaml, sort_keys=False, allow_unicode=True), encoding="utf-8")
    console.print(f"[green]已写入[/green] {gateway_file}")

    # Write config.yaml (agent settings)
    agent_config = {
        "model": {
            "default": llm_config.get("model", "anthropic/claude-sonnet-4"),
        },
        "context": {
            "auto_compact_threshold": 0.8,
            "max_turns": 50,
        },
        "memory": {
            "enabled": True,
            "scope": "project",
        },
        "logging": {
            "level": "info",
            "trajectory": True,
            "trajectory_path": str(home / "trajectories"),
        },
    }

    config_file = _config_path()
    config_file.write_text(yaml.safe_dump(agent_config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    console.print(f"[green]已写入[/green] {config_file}")


def _print_summary(
    ws: Path,
    profile: dict[str, str],
    llm_config: dict[str, Any],
    platforms: dict[str, Any],
    gateway_settings: dict[str, Any],
) -> None:
    console.print("\n" + "=" * 60)
    console.print("[bold green]配置完成！[/bold green]")
    console.print("=" * 60 + "\n")

    home = _myagent_home()
    console.print(f"[bold]工作区：[/bold]   {home}")
    console.print(f"  [dim]- soul.md、user.md、identity.md[/dim]")
    console.print(f"  [dim]- memory/（持久化记忆）[/dim]")
    console.print(f"  [dim]- projects/（项目工作区）[/dim]")
    console.print(f"  [dim]- sessions/（对话历史）[/dim]")
    console.print(f"[bold]配置：[/bold]      {home / 'config.yaml'}")
    console.print(f"[bold]网关：[/bold]     {home / 'gateway.yaml'}")
    console.print(f"[bold]环境：[/bold]         {home / '.env'}")
    console.print()

    if profile.get("name"):
        console.print(f"[bold]用户：[/bold]        {profile['name']}（{profile.get('role', '未知')}）")
    else:
        console.print("[yellow]用户：[/yellow]        未设置画像（稍后请编辑 user.md）")

    if llm_config.get("provider"):
        console.print(f"[bold]LLM：[/bold]         {llm_config['provider']} / {llm_config.get('model', 'default')}")
    else:
        console.print("[yellow]LLM：[/yellow]         未配置")

    if platforms:
        console.print(f"[bold]平台：[/bold]   {', '.join(platforms.keys())}")
    else:
        console.print("[yellow]平台：[/yellow]   无（仅 Webhook）")

    console.print(f"[bold]重置模式：[/bold]  {gateway_settings['session_reset_mode']}")
    console.print()

    console.print(Panel(
        "[bold]下一步：[/bold]\n"
        "1. 加载环境变量：[cyan]source ~/.myagent/.env[/cyan]\n"
        "2. 启动网关：   [cyan]myagent gateway[/cyan]\n"
        "3. 启动 Web UI：[cyan]myagent web[/cyan]\n"
        "4. 或使用 TUI： [cyan]myagent --tui[/cyan]\n"
        "\n"
        "[dim]编辑 ~/.myagent/user.md 更新您的画像。[/dim]\n"
        "[dim]编辑 ~/.myagent/gateway.yaml 添加更多平台。[/dim]\n"
        "[dim]编辑 ~/.myagent/.env 修改 API 密钥。[/dim]",
        border_style="green",
    ))


def run_wizard() -> None:
    """Run the interactive initialization wizard."""
    _print_header()

    if not _step_welcome():
        console.print("[yellow]配置已取消。随时可运行 `myagent init` 重新启动。[/yellow]")
        return

    ws = _step_workspace()
    profile = _step_user_profile(ws)
    llm_config = _step_llm_provider()
    platforms = _step_gateway_platforms()
    gateway_settings = _step_gateway_settings()
    _write_config(llm_config, platforms, gateway_settings)
    _print_summary(ws, profile, llm_config, platforms, gateway_settings)
