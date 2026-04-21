"""CLI for MyAgent."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from myagent import __version__

def _version_callback(value: bool) -> None:
    if value:
        console = Console()
        console.print(f"MyAgent version {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="myagent",
    help="MyAgent - An AI-powered coding assistant",
    add_completion=False,
)
console = Console()


def _print_welcome() -> None:
    welcome_text = f"""
# Welcome to MyAgent v{__version__}

Type your message and press Enter to chat.
Type **/exit** or **/quit** to leave.
Type **/help** for available commands.
"""
    console.print(Markdown(welcome_text))


@app.command()
def init(
    quick: bool = typer.Option(False, "--quick", "-q", help="Quick mode — skip prompts, use defaults"),
) -> None:
    """Initialize MyAgent configuration and workspace."""
    from myagent.init.wizard import run_wizard
    run_wizard()


@app.command()
def doctor() -> None:
    """Diagnose MyAgent configuration issues."""
    from myagent.init.doctor import run_doctor
    run_doctor()


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
) -> None:
    """Start the MyAgent Web UI server."""
    import uvicorn
    from myagent.web.server import create_app

    console.print(f"[bold green]Starting MyAgent Web UI on http://{host}:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


@app.command()
def gateway(
    port: int = typer.Option(18789, "--port", "-p", help="Gateway WebSocket port"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Start the MyAgent Gateway server."""
    console.print(f"[bold green]Starting MyAgent Gateway on port {port}[/bold green]")
    console.print("[yellow]Note: Gateway server implementation is a placeholder.[/yellow]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")


@app.command()
def main(
    agent: str = typer.Option("general", "--agent", "-a", help="Agent to use"),
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="Single prompt mode"),
    tui: bool = typer.Option(False, "--tui", "-t", help="Use TUI interface"),
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version"
    ),
) -> None:
    """Start an interactive session with MyAgent."""
    if tui:
        from myagent.tui.app import run_tui
        run_tui()
        return

    from myagent.agents.loader import AgentLoader
    from myagent.engine.query_engine import QueryEngine
    from myagent.tools.bash import Bash
    from myagent.tools.edit import Edit
    from myagent.tools.glob import Glob
    from myagent.tools.grep import Grep
    from myagent.tools.read import Read
    from myagent.tools.registry import ToolRegistry
    from myagent.tools.write import Write

    loader = AgentLoader()
    agents = loader.load_builtin_agents()
    agent_def = agents.get(agent, agents.get("general"))

    if agent_def is None:
        console.print(f"[red]Agent '{agent}' not found.[/red]")
        raise typer.Exit(1)

    registry = ToolRegistry()
    registry.register(Read())
    registry.register(Write())
    registry.register(Edit())
    registry.register(Bash())
    registry.register(Glob())
    registry.register(Grep())

    engine = QueryEngine(
        tool_registry=registry,
        system_prompt=agent_def.system_prompt or "You are a helpful assistant.",
    )

    if prompt:
        console.print(f"[bold blue]> {prompt}[/bold blue]")
        console.print("[yellow]Note: LLM client not configured. This is a placeholder.[/yellow]")
        return

    _print_welcome()
    console.print(Panel(f"Using agent: [bold]{agent_def.name}[/bold]", border_style="green"))

    while True:
        try:
            user_input = console.input("[bold green]> [/bold green]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input in ("/exit", "/quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input == "/help":
            console.print(Markdown("""
## Available Commands

- `/exit` or `/quit` - Exit the session
- `/help` - Show this help message
"""))
            continue

        console.print(f"[dim]You: {user_input}[/dim]")
        console.print("[yellow]Note: LLM client not configured. This is a placeholder.[/yellow]")


def _entry() -> None:
    app()
