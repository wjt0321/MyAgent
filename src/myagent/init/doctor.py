"""Configuration doctor for MyAgent.

Diagnoses common setup issues and suggests fixes.
Inspired by OpenClaw's `doctor` command.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from myagent import __version__
from myagent.gateway.base import Platform

console = Console()


def _myagent_home() -> Path:
    home = os.getenv("MYAGENT_HOME")
    if home:
        return Path(home)
    return Path.home() / ".myagent"


def _check_file_exists(path: Path, name: str) -> tuple[bool, str]:
    if path.exists():
        return True, f"[green]{name} found[/green] at {path}"
    return False, f"[red]{name} missing[/red] — run `myagent init`"


def _check_env_var(name: str, secret: bool = False) -> tuple[bool, str]:
    value = os.getenv(name)
    if value:
        display = value[:8] + "..." if secret and len(value) > 8 else value
        return True, f"[green]{name}={display}[/green]"
    return False, f"[red]{name} not set[/red]"


def _check_llm_provider() -> list[tuple[bool, str]]:
    results: list[tuple[bool, str]] = []

    providers = [
        ("OPENAI_API_KEY", "OpenAI"),
        ("ANTHROPIC_API_KEY", "Anthropic"),
        ("DEEPSEEK_API_KEY", "DeepSeek"),
        ("GEMINI_API_KEY", "Google Gemini"),
        ("QWEN_API_KEY", "Alibaba Qwen"),
        ("SILICONFLOW_API_KEY", "SiliconFlow"),
        ("AZURE_OPENAI_API_KEY", "Azure OpenAI"),
        ("OPENROUTER_API_KEY", "OpenRouter"),
    ]

    any_found = False
    for env_name, label in providers:
        ok, msg = _check_env_var(env_name, secret=True)
        if ok:
            any_found = True
            results.append((ok, f"{label}: {msg}"))

    if not any_found:
        results.append((False, "[red]No LLM API key found[/red] — set one in ~/.myagent/.env"))

    return results


def _check_gateway_config() -> list[tuple[bool, str]]:
    results: list[tuple[bool, str]] = []
    gateway_path = _myagent_home() / "gateway.yaml"

    if not gateway_path.exists():
        results.append((False, "[red]gateway.yaml missing[/red]"))
        return results

    try:
        data = yaml.safe_load(gateway_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        results.append((False, f"[red]gateway.yaml invalid YAML: {e}[/red]"))
        return results

    platforms = data.get("platforms", {})
    if not platforms:
        results.append((True, "[yellow]No platforms configured[/yellow] (Webhook-only mode)"))
    else:
        for name, cfg in platforms.items():
            if cfg.get("enabled"):
                results.append((True, f"[green]{name} enabled[/green]"))
            else:
                results.append((True, f"[yellow]{name} disabled[/yellow]"))

    return results


def _check_directories() -> list[tuple[bool, str]]:
    results: list[tuple[bool, str]] = []
    home = _myagent_home()

    for subdir in ["sessions", "logs", "workspace"]:
        path = home / subdir
        if path.exists():
            results.append((True, f"[green]{subdir}/[/green] exists"))
        else:
            results.append((False, f"[red]{subdir}/[/red] missing — run `myagent init`"))

    return results


def run_doctor() -> None:
    """Run the configuration doctor."""
    console.print(Panel.fit(
        f"[bold cyan]MyAgent v{__version__}[/bold cyan] — Configuration Doctor",
        border_style="cyan",
    ))

    all_checks: list[tuple[str, list[tuple[bool, str]]]] = []

    # Directories
    all_checks.append(("Directories", _check_directories()))

    # Config files
    file_checks: list[tuple[bool, str]] = []
    home = _myagent_home()
    for name, path in [
        ("config.yaml", home / "config.yaml"),
        ("gateway.yaml", home / "gateway.yaml"),
        (".env", home / ".env"),
    ]:
        file_checks.append(_check_file_exists(path, name))
    all_checks.append(("Config Files", file_checks))

    # LLM
    all_checks.append(("LLM Provider", _check_llm_provider()))

    # Gateway
    all_checks.append(("Gateway Platforms", _check_gateway_config()))

    # Display results
    table = Table(title="Check Results")
    table.add_column("Category", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Detail")

    total_ok = 0
    total_fail = 0

    for category, checks in all_checks:
        for ok, detail in checks:
            status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
            if ok:
                total_ok += 1
            else:
                total_fail += 1
            table.add_row(category, status, detail)
            category = ""  # Only show category on first row

    console.print()
    console.print(table)
    console.print()

    if total_fail == 0:
        console.print(Panel(
            "[bold green]All checks passed![/bold green] MyAgent is ready to use.",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold yellow]{total_fail} issue(s) found.[/bold yellow]\n"
            "Run [cyan]myagent init[/cyan] to set up missing configs,\n"
            "or edit files in [cyan]~/.myagent/[/cyan] directly.",
            border_style="yellow",
        ))
