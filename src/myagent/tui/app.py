"""MyAgent TUI application using Textual."""

from __future__ import annotations

import os
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Input, RichLog, Static

from myagent.agents.loader import AgentLoader
from myagent.engine.messages import ConversationMessage, TextBlock
from myagent.llm.providers.anthropic import AnthropicProvider
from myagent.llm.types import DoneChunk, TextChunk


def _get_env_or_prompt(key: str, default: str | None = None) -> str | None:
    """Get configuration from environment variable."""
    return os.environ.get(key, default)


class MyAgentApp(App[None]):
    """MyAgent TUI application."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #header {
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
    }

    #transcript-container {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }

    #transcript {
        height: 100%;
        background: $surface;
    }

    #current-response {
        height: auto;
        max-height: 5;
        background: $surface-darken-1;
        color: $text-muted;
        padding: 0 1;
    }

    #composer-container {
        height: 3;
        border: solid $primary;
    }

    #composer {
        height: 100%;
        border: none;
        padding: 0 1;
    }

    #footer {
        height: 1;
    }
    """

    BINDINGS = [
        ("ctrl+l", "clear", "Clear"),
        ("ctrl+d", "quit", "Exit"),
    ]

    current_agent = reactive("general")
    current_provider = reactive("anthropic")

    def __init__(self) -> None:
        super().__init__()
        self._transcript_lines: list[str] = []
        self._current_response_text = ""
        self._agent_loader = AgentLoader()
        self._agents = self._agent_loader.load_builtin_agents()
        self._conversation_history: list[ConversationMessage] = []
        self._provider: AnthropicProvider | None = None
        self._init_provider()

    def _init_provider(self) -> None:
        """Initialize LLM provider from environment variables."""
        api_key = _get_env_or_prompt("ZHIPU_API_KEY")
        if not api_key:
            api_key = _get_env_or_prompt("ANTHROPIC_API_KEY")
        if not api_key:
            api_key = _get_env_or_prompt("MYAGENT_API_KEY")

        model = _get_env_or_prompt("ZHIPU_MODEL", "glm-4.7")
        base_url = _get_env_or_prompt("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/anthropic")

        if api_key:
            self._provider = AnthropicProvider(
                api_key=api_key,
                model=model,
                base_url=base_url,
            )
            self.current_provider = f"zhipu/{model}"
        else:
            self.current_provider = "none (set ZHIPU_API_KEY)"

    def compose(self) -> ComposeResult:
        yield Static(
            f"MyAgent v0.2.0 | Agent: {self.current_agent} | Provider: {self.current_provider}",
            id="header",
        )

        with Vertical(id="transcript-container"):
            yield RichLog(id="transcript", highlight=True, markup=True)

        yield Static("", id="current-response")

        with Horizontal(id="composer-container"):
            yield Input(placeholder="Type a message or /command...", id="composer")

        yield Footer(id="footer")

    def on_mount(self) -> None:
        self.query_one("#composer", Input).focus()
        if self._provider is None:
            self.add_assistant_message(
                "Welcome to MyAgent!\n"
                "[yellow]Warning: No API key configured.[/yellow] "
                "Set ZHIPU_API_KEY environment variable to enable LLM responses.\n"
                "Type /help for commands."
            )
        else:
            self.add_assistant_message(
                "Welcome to MyAgent! Type a message to start chatting, or use /help for commands."
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        value = event.value.strip()
        if not value:
            return

        event.input.value = ""

        if value.startswith("/"):
            self._handle_command(value)
        else:
            self.add_user_message(value)
            self._handle_user_message(value)

    def _handle_command(self, command: str) -> None:
        """Handle slash commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/exit" or cmd == "/quit":
            self.exit()
        elif cmd == "/clear":
            self.clear_transcript()
        elif cmd == "/help":
            self.add_assistant_message(self._get_help_text())
        elif cmd == "/agent":
            if len(parts) > 1:
                self._switch_agent(parts[1])
            else:
                agents = ", ".join(self._agents.keys())
                self.add_assistant_message(f"Available agents: {agents}")
        elif cmd == "/provider":
            if len(parts) > 1:
                self.current_provider = parts[1]
                self._update_header()
                self.add_assistant_message(f"Switched to provider: {parts[1]}")
            else:
                self.add_assistant_message("Usage: /provider <name>")
        elif cmd == "/model":
            if len(parts) > 1:
                self._switch_model(parts[1])
            else:
                self.add_assistant_message("Usage: /model <name> (e.g., glm-4.7, glm-5.1)")
        else:
            self.add_assistant_message(f"Unknown command: {cmd}. Type /help for available commands.")

    async def _handle_user_message(self, message: str) -> None:
        """Process user message with real LLM streaming."""
        if self._provider is None:
            self.add_assistant_message(
                "[red]Error: No LLM provider configured.[/red]\n"
                "Set ZHIPU_API_KEY environment variable and restart."
            )
            return

        self.update_current_response("Thinking...")

        user_msg = ConversationMessage(
            role="user",
            content=[TextBlock(text=message)],
        )
        self._conversation_history.append(user_msg)

        full_response = ""
        try:
            async for chunk in self._provider.stream_messages(self._conversation_history):
                if isinstance(chunk, TextChunk):
                    full_response += chunk.text
                    self.update_current_response(full_response)
                elif isinstance(chunk, DoneChunk):
                    break

            self.update_current_response("")
            self.add_assistant_message(full_response)

            assistant_msg = ConversationMessage(
                role="assistant",
                content=[TextBlock(text=full_response)],
            )
            self._conversation_history.append(assistant_msg)

        except Exception as e:
            self.update_current_response("")
            self.add_assistant_message(f"[red]Error: {type(e).__name__}: {e}[/red]")

    def _switch_agent(self, agent_name: str) -> None:
        """Switch to a different agent."""
        if agent_name in self._agents:
            self.current_agent = agent_name
            self._update_header()
            self.add_assistant_message(f"Switched to agent: {agent_name}")
        else:
            available = ", ".join(self._agents.keys())
            self.add_assistant_message(f"Unknown agent '{agent_name}'. Available: {available}")

    def _switch_model(self, model_name: str) -> None:
        """Switch to a different model."""
        if self._provider is None:
            self.add_assistant_message("[red]Error: No provider configured.[/red]")
            return

        self._provider.model = model_name
        self.current_provider = f"zhipu/{model_name}"
        self._update_header()
        self.add_assistant_message(f"Switched to model: {model_name}")

    def _update_header(self) -> None:
        """Update header text."""
        header = self.query_one("#header", Static)
        header.update(
            f"MyAgent v0.2.0 | Agent: {self.current_agent} | Provider: {self.current_provider}"
        )

    def add_user_message(self, message: str) -> None:
        """Add a user message to the transcript."""
        self._add_line(f"[bold blue]You:[/bold blue] {message}")

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the transcript."""
        self._add_line(f"[bold green]Agent:[/bold green] {message}")

    def add_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Add a tool call to the transcript."""
        args_str = ", ".join(f"{k}={v}" for k, v in arguments.items())
        self._add_line(f"[bold yellow]Tool:[/bold yellow] {tool_name}({args_str})")

    def add_tool_result(self, result: str, is_error: bool = False) -> None:
        """Add a tool result to the transcript."""
        color = "red" if is_error else "cyan"
        self._add_line(f"[bold {color}]Result:[/bold {color}] {result}")

    def update_current_response(self, text: str) -> None:
        """Update the current response display."""
        self._current_response_text = text
        response_widget = self.query_one("#current-response", Static)
        response_widget.update(Text(text))

    def clear_transcript(self) -> None:
        """Clear the transcript and conversation history."""
        self._transcript_lines = []
        self._conversation_history = []
        transcript = self.query_one("#transcript", RichLog)
        transcript.clear()

    def _add_line(self, line: str) -> None:
        """Add a line to the transcript."""
        self._transcript_lines.append(line)
        transcript = self.query_one("#transcript", RichLog)
        transcript.write(line)

    def action_clear(self) -> None:
        """Action handler for Ctrl+L."""
        self.clear_transcript()

    def _get_help_text(self) -> str:
        """Get help text for commands."""
        return """Available commands:
  /exit, /quit  - Exit MyAgent
  /clear        - Clear the transcript
  /help         - Show this help message
  /agent <name> - Switch to a different agent
  /provider <n> - Switch LLM provider
  /model <name> - Switch LLM model (e.g., glm-4.7, glm-5.1)

Keyboard shortcuts:
  Ctrl+L - Clear transcript
  Ctrl+D - Exit"""


def run_tui() -> None:
    """Run the MyAgent TUI application."""
    app = MyAgentApp()
    app.run()
