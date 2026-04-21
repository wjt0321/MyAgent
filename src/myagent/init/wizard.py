"""Interactive initialization wizard for MyAgent.

Guides users through first-time setup: config, LLM provider, Gateway platforms.
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
        f"[bold cyan]MyAgent v{__version__}[/bold cyan] — Initialization Wizard\n"
        "[dim]This wizard will guide you through the first-time setup.[/dim]",
        border_style="cyan",
    ))


def _step_welcome() -> bool:
    console.print("\n[bold]Welcome![/bold] Let's get MyAgent ready to use.\n")
    console.print("The wizard will:")
    console.print("  1. Create the MyAgent home directory")
    console.print("  2. Configure your LLM provider (OpenAI, Anthropic, etc.)")
    console.print("  3. Set up Gateway platforms (Feishu, Slack, Discord, etc.)")
    console.print("  4. Generate config files and environment variables\n")
    return Confirm.ask("Continue with setup?", default=True)


def _step_directories() -> None:
    home = _myagent_home()
    dirs = [
        home,
        home / "sessions",
        home / "logs",
        home / "workspace",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Created[/green] {home}")


def _step_llm_provider() -> dict[str, Any]:
    console.print("\n[bold]Step 1: LLM Provider Configuration[/bold]")
    console.print("MyAgent needs an LLM to power conversations.\n")

    providers = {
        "1": ("openai", "OpenAI (GPT-4o, GPT-4o-mini)"),
        "2": ("anthropic", "Anthropic (Claude 3.5/4 Sonnet, Opus)"),
        "3": ("deepseek", "DeepSeek (V3, R1)"),
        "4": ("gemini", "Google Gemini (1.5 Pro, Flash)"),
        "5": ("qwen", "Alibaba Qwen (Qwen-Max, Plus)"),
        "6": ("siliconflow", "SiliconFlow (aggregated Chinese models)"),
        "7": ("ollama", "Ollama (local models — llama3, mistral, etc.)"),
        "8": ("azure", "Azure OpenAI Service"),
        "9": ("openrouter", "OpenRouter (unified API for many models)"),
        "0": ("skip", "Skip for now — configure later"),
    }

    for key, (_, label) in providers.items():
        console.print(f"  [{key}] {label}")

    choice = Prompt.ask(
        "\nSelect provider",
        choices=list(providers.keys()),
        default="2",
    )

    provider_id, _ = providers[choice]

    if provider_id == "skip":
        console.print("[yellow]Skipped LLM config. Set MYAGENT_* env vars later.[/yellow]")
        return {}

    api_key = Prompt.ask(f"Enter your {provider_id.upper()} API key", password=True)

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
    model = Prompt.ask("Default model", default=default_model)

    result: dict[str, Any] = {
        "provider": provider_id,
        "api_key": api_key,
        "model": model,
    }

    if provider_id == "ollama":
        base_url = Prompt.ask("Ollama base URL", default="http://localhost:11434")
        result["base_url"] = base_url

    if provider_id == "azure":
        azure_endpoint = Prompt.ask("Azure endpoint URL")
        result["azure_endpoint"] = azure_endpoint
        result["api_version"] = Prompt.ask("API version", default="2024-08-01-preview")

    console.print(f"[green]Configured[/green] {provider_id} -> {model}")
    return result


def _step_gateway_platforms() -> dict[str, Any]:
    console.print("\n[bold]Step 2: Gateway Platforms[/bold]")
    console.print(
        "MyAgent can receive messages from messaging platforms.\n"
        "Enable the ones you want to connect (you can add more later).\n"
    )

    platforms: dict[str, Any] = {}

    if Confirm.ask("Enable [bold]Feishu/Lark[/bold] (飞书)?", default=False):
        app_id = Prompt.ask("  Feishu App ID")
        app_secret = Prompt.ask("  Feishu App Secret", password=True)
        platforms["feishu"] = {
            "enabled": True,
            "app_id": app_id,
            "app_secret": app_secret,
        }
        console.print("  [green]Feishu configured[/green]")

    if Confirm.ask("Enable [bold]Slack[/bold]?", default=False):
        token = Prompt.ask("  Slack Bot Token (xoxb-...)", password=True)
        platforms["slack"] = {
            "enabled": True,
            "token": token,
        }
        console.print("  [green]Slack configured[/green]")

    if Confirm.ask("Enable [bold]Discord[/bold]?", default=False):
        token = Prompt.ask("  Discord Bot Token", password=True)
        platforms["discord"] = {
            "enabled": True,
            "token": token,
        }
        console.print("  [green]Discord configured[/green]")

    if Confirm.ask("Enable [bold]Telegram[/bold]?", default=False):
        token = Prompt.ask("  Telegram Bot Token", password=True)
        platforms["telegram"] = {
            "enabled": True,
            "token": token,
        }
        console.print("  [green]Telegram configured[/green]")

    if Confirm.ask("Enable [bold]DingTalk[/bold] (钉钉)?", default=False):
        client_id = Prompt.ask("  DingTalk Client ID")
        client_secret = Prompt.ask("  DingTalk Client Secret", password=True)
        platforms["dingtalk"] = {
            "enabled": True,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        console.print("  [green]DingTalk configured[/green]")

    if not platforms:
        console.print("[yellow]No platforms enabled. Gateway will start in Webhook-only mode.[/yellow]")

    return platforms


def _step_gateway_settings() -> dict[str, Any]:
    console.print("\n[bold]Step 3: Gateway Settings[/bold]")

    webhook_secret = secrets.token_urlsafe(32)
    console.print(f"Generated webhook secret: [dim]{webhook_secret[:8]}...[/dim]")

    session_reset = Prompt.ask(
        "Session reset mode",
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
    env_lines = ["# MyAgent Environment Configuration", f"# Generated by myagent init v{__version__}"]

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

    env_lines.append(f"\n# Gateway Settings")
    env_lines.append(f"WEBHOOK_SECRET={gateway_settings['webhook_secret']}")

    env_file = _env_path()
    env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    console.print(f"[green]Wrote[/green] {env_file}")

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
    console.print(f"[green]Wrote[/green] {gateway_file}")

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
    console.print(f"[green]Wrote[/green] {config_file}")


def _print_summary(
    llm_config: dict[str, Any],
    platforms: dict[str, Any],
    gateway_settings: dict[str, Any],
) -> None:
    console.print("\n" + "=" * 60)
    console.print("[bold green]Setup Complete![/bold green]")
    console.print("=" * 60 + "\n")

    home = _myagent_home()
    console.print(f"[bold]MyAgent Home:[/bold] {home}")
    console.print(f"[bold]Config:[/bold]      {home / 'config.yaml'}")
    console.print(f"[bold]Gateway:[/bold]     {home / 'gateway.yaml'}")
    console.print(f"[bold]Env:[/bold]         {home / '.env'}")
    console.print(f"[bold]Sessions:[/bold]    {home / 'sessions'}")
    console.print(f"[bold]Logs:[/bold]        {home / 'logs'}")
    console.print()

    if llm_config.get("provider"):
        console.print(f"[bold]LLM:[/bold]         {llm_config['provider']} / {llm_config.get('model', 'default')}")
    else:
        console.print("[yellow]LLM:[/yellow]         Not configured")

    if platforms:
        console.print(f"[bold]Platforms:[/bold]   {', '.join(platforms.keys())}")
    else:
        console.print("[yellow]Platforms:[/yellow]   None (Webhook-only)")

    console.print(f"[bold]Reset mode:[/bold]  {gateway_settings['session_reset_mode']}")
    console.print()

    console.print(Panel(
        "[bold]Next Steps:[/bold]\n"
        "1. Source the env file: [cyan]source ~/.myagent/.env[/cyan]\n"
        "2. Start the Gateway:   [cyan]myagent gateway[/cyan]\n"
        "3. Start the Web UI:    [cyan]myagent web[/cyan]\n"
        "4. Or use the TUI:      [cyan]myagent --tui[/cyan]\n"
        "\n"
        "[dim]Edit ~/.myagent/gateway.yaml to add more platforms.[/dim]\n"
        "[dim]Edit ~/.myagent/.env to change API keys.[/dim]",
        border_style="green",
    ))


def run_wizard() -> None:
    """Run the interactive initialization wizard."""
    _print_header()

    if not _step_welcome():
        console.print("[yellow]Setup cancelled. Run `myagent init` anytime to restart.[/yellow]")
        return

    _step_directories()
    llm_config = _step_llm_provider()
    platforms = _step_gateway_platforms()
    gateway_settings = _step_gateway_settings()
    _write_config(llm_config, platforms, gateway_settings)
    _print_summary(llm_config, platforms, gateway_settings)
