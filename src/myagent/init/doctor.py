"""Configuration doctor for MyAgent."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from myagent import __version__
from myagent.init.status import get_setup_status

console = Console()


def run_doctor() -> None:
    """Run the configuration doctor."""
    status = get_setup_status()

    console.print(
        Panel.fit(
            f"[bold cyan]MyAgent v{__version__}[/bold cyan] — Configuration Doctor",
            border_style="cyan",
        )
    )

    table = Table(title="Setup Status")
    table.add_column("检查项", style="cyan")
    table.add_column("状态", style="bold")
    table.add_column("说明")

    checks = [
        ("Workspace", status.workspace_ready, "工作区目录是否齐全"),
        ("Config", status.config_ready, "config.yaml 是否存在且可解析"),
        ("Env", status.env_ready, ".env 是否存在"),
        ("LLM", status.llm_ready, "是否检测到可用的 API Key"),
        ("Gateway", status.gateway_ready, "gateway.yaml 是否存在且可解析"),
    ]

    for name, ok, detail in checks:
        table.add_row(name, "[green]OK[/green]" if ok else "[red]FAIL[/red]", detail)

    console.print()
    console.print(table)
    console.print()

    if status.issues:
        issues = Table(title="问题 -> 修复动作")
        issues.add_column("问题", style="red")
        issues.add_column("修复动作", style="yellow")
        for issue in status.issues:
            issues.add_row(issue.summary, issue.fix)
        console.print(issues)
        console.print()

    if status.overall_ready:
        console.print(
            Panel(
                "[bold green]MyAgent 已准备就绪。[/bold green]\n"
                "建议下一步： [cyan]myagent --tui[/cyan] 或 [cyan]myagent web[/cyan]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[bold yellow]Setup Required[/bold yellow]\n"
                f"建议下一步： [cyan]{status.next_action}[/cyan]",
                border_style="yellow",
            )
        )
