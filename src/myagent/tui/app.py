"""MyAgent TUI application using Textual."""

from __future__ import annotations

import os
from typing import Any

import yaml
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, RichLog, Static, TextArea

from myagent.agents.loader import AgentLoader
from myagent.cost.tracker import CostTracker
from myagent.engine.messages import ConversationMessage
from myagent.engine.query_engine import QueryEngine
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    PermissionRequestEvent,
    PermissionResultEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.init.status import SetupStatus, get_myagent_home, get_setup_status
from myagent.llm.providers.anthropic import AnthropicProvider
from myagent.memory.manager import MemoryManager
from myagent.security.checker import PermissionChecker
from myagent.tools.bash import Bash
from myagent.tools.edit import Edit
from myagent.tools.glob import Glob
from myagent.tools.grep import Grep
from myagent.tools.read import Read
from myagent.tools.registry import ToolRegistry
from myagent.tools.write import Write
from myagent.tui.logo import get_logo
from myagent.tui.screens import CommandPaletteScreen, InfoModalScreen, PermissionModalScreen


def _get_env_or_prompt(key: str, default: str | None = None) -> str | None:
    """Get configuration from environment variable."""
    return os.environ.get(key, default)


def _create_tool_registry(tool_names: list[str] | None = None) -> ToolRegistry:
    """Create a tool registry with specified tools (or all by default)."""
    all_tools: dict[str, Any] = {
        "Read": Read(),
        "Bash": Bash(),
        "Edit": Edit(),
        "Write": Write(),
        "Glob": Glob(),
        "Grep": Grep(),
    }

    registry = ToolRegistry()
    if tool_names is None:
        for tool in all_tools.values():
            registry.register(tool)
    else:
        for name in tool_names:
            if name in all_tools:
                registry.register(all_tools[name])

    return registry


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

    #main-content {
        height: 1fr;
    }

    #side-panel {
        width: 36;
        border: solid $primary;
        background: $surface-darken-1;
        padding: 0 1;
    }

    .panel-title {
        text-style: bold;
        color: $accent;
        margin: 1 0 0 0;
    }

    .panel-body {
        color: $text-muted;
        margin: 0 0 1 0;
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
        height: 5;
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
        ("ctrl+k", "command_palette", "Palette"),
        ("ctrl+d", "quit", "Exit"),
        ("ctrl+r", "regenerate", "Regenerate"),
        ("enter", "submit_message", "Send"),
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
        self._tool_registry = _create_tool_registry()
        self._permission_checker = PermissionChecker()
        self._cost_tracker = CostTracker()
        self._query_engine: QueryEngine | None = None
        self._turn_count = 0
        self._last_user_message = ""
        self._current_agent_def = self._agents.get("general")
        self._memory_manager = MemoryManager(
            memory_dir=get_myagent_home() / "memory"
        )
        self._config_path = get_myagent_home() / "config.yaml"
        self._config: dict[str, Any] = {}
        self.setup_status: SetupStatus = get_setup_status()
        self._workspace_path = str(get_myagent_home())
        self._activity_state: dict[str, str] = {
            "status": "idle",
            "tool_name": "none",
            "tool_use_id": "-",
            "detail": "暂无工具执行",
        }
        self._task_status: dict[str, str] = {
            "state": "idle",
            "request": "",
            "detail": "暂无任务",
        }
        self.current_model = "unconfigured"
        self._load_config()
        self._init_provider()

    def _init_provider(self) -> None:
        """Initialize LLM provider and QueryEngine from environment variables."""
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
            self.current_model = model
            self._query_engine = QueryEngine(
                tool_registry=self._tool_registry,
                llm_client=self._provider,
                system_prompt="You are a helpful assistant.",
                permission_checker=self._permission_checker,
            )
        else:
            self.current_provider = "none (set ZHIPU_API_KEY)"
            self.current_model = self._config.get("model", "unconfigured")

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Static(
            (
                "MyAgent Workbench v0.2.0 | "
                f"Agent: {self.current_agent} | Model: {self.current_model} | "
                f"Provider: {self.current_provider}"
            ),
            id="header",
        )

        with Horizontal(id="main-content"):
            with Vertical(id="transcript-container"):
                yield RichLog(id="transcript", highlight=True, markup=True)

            with Vertical(id="side-panel"):
                yield Static("状态概览", classes="panel-title")
                yield Static("", id="status-panel", classes="panel-body")
                yield Static("任务状态", classes="panel-title")
                yield Static("", id="task-panel", classes="panel-body")
                yield Static("活动轨迹", classes="panel-title")
                yield Static("", id="activity-panel", classes="panel-body")
                yield Static("当前响应", classes="panel-title")
                yield Static("", id="current-response", classes="panel-body")

        with Horizontal(id="composer-container"):
            yield TextArea(
                placeholder="Type a message or /command... (Shift+Enter for new line)",
                id="composer",
                show_line_numbers=False,
            )

        yield Footer(id="footer")

    def on_mount(self) -> None:
        """Initialize focus and startup messages."""
        self.query_one("#composer", TextArea).focus()
        self._refresh_side_panel()

        # Display ASCII logo on startup
        import shutil
        term_width = shutil.get_terminal_size().columns
        logo = get_logo(term_width)
        self.add_assistant_message(f"[dim]{logo}[/dim]")

        if not self.setup_status.overall_ready:
            self.add_assistant_message(self._get_setup_required_text())
        elif self._query_engine is None:
            self.add_assistant_message(
                "[yellow]Warning: No API key configured.[/yellow] "
                "Set ZHIPU_API_KEY environment variable to enable LLM responses.\n"
                "Type /help for commands."
            )
        else:
            self.add_assistant_message(
                "Welcome! Type a message to start chatting, or use /help for commands."
            )

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area changes - not used directly."""
        pass

    def action_submit_message(self) -> None:
        """Submit the current message from TextArea."""
        composer = self.query_one("#composer", TextArea)
        value = composer.text.strip()
        if not value:
            return

        # Check if Shift+Enter was used (multiline mode)
        # In TextArea, plain Enter submits, Shift+Enter creates newline
        # The newline is already in the text, so we just check for non-empty
        composer.text = ""

        if value.startswith("/"):
            self._handle_command(value)
        else:
            self.add_user_message(value)
            self._last_user_message = value
            self.run_worker(self._handle_user_message(value))

    def action_regenerate(self) -> None:
        """Regenerate the last assistant response."""
        if not hasattr(self, '_last_user_message') or not self._last_user_message:
            self.add_assistant_message("[yellow]No previous message to regenerate.[/yellow]")
            return

        if self._query_engine is None:
            self.add_assistant_message("[red]Error: No LLM provider configured.[/red]")
            return

        # Remove the last assistant message from history
        if self._query_engine.messages and len(self._query_engine.messages) >= 2:
            # Find and remove the last user message and assistant response
            # Keep system prompt and earlier messages
            last_user_idx = None
            for i in range(len(self._query_engine.messages) - 1, -1, -1):
                if self._query_engine.messages[i].role == "user":
                    last_user_idx = i
                    break

            if last_user_idx is not None:
                # Remove messages from last user onwards
                self._query_engine.messages = self._query_engine.messages[:last_user_idx]
                self.add_assistant_message("[dim]Regenerating response...[/dim]")
                self.run_worker(self._handle_user_message(self._last_user_message))
            else:
                self.add_assistant_message(
                    "[yellow]Could not find previous message to regenerate.[/yellow]"
                )
        else:
            self.add_assistant_message(
                "[yellow]Not enough conversation history to regenerate.[/yellow]"
            )

    def _handle_command(self, command: str) -> None:
        """Handle slash commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/exit" or cmd == "/quit":
            self.exit()
        elif cmd == "/clear":
            self.clear_transcript()
        elif cmd == "/help":
            self._open_info_modal("Help", self._get_help_text())
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
                self.add_assistant_message(
                    "Usage: /model <name> (e.g., glm-4.7, glm-5.1)"
                )
        elif cmd == "/memory":
            self._show_memory()
        elif cmd == "/tokens":
            self._show_token_stats()
        elif cmd == "/plan":
            request = " ".join(parts[1:]).strip()
            if request:
                self._start_plan_flow(request)
            else:
                self._open_info_modal("Plan", "用法：/plan <任务描述>")
        elif cmd == "/setup":
            self.setup_status = get_setup_status()
            self._open_info_modal("Setup Required", self._get_setup_required_text())
        elif cmd == "/doctor":
            self.setup_status = get_setup_status()
            self._open_info_modal(
                "Doctor Summary",
                "[bold]Doctor Summary[/bold]\n"
                f"Workspace: {'OK' if self.setup_status.workspace_ready else 'FAIL'}\n"
                f"Config: {'OK' if self.setup_status.config_ready else 'FAIL'}\n"
                f"LLM: {'OK' if self.setup_status.llm_ready else 'FAIL'}\n"
                f"Next: {self.setup_status.next_action}",
            )
        elif cmd == "/session":
            self._open_info_modal("Session Summary", self._get_session_summary())
        else:
            self.add_assistant_message(
                f"Unknown command: {cmd}. Type /help for available commands."
            )

    def _show_token_stats(self) -> None:
        """Show token usage statistics."""
        if self._query_engine is None or not self._query_engine.auto_compactor:
            self.add_assistant_message("[yellow]Token stats not available.[/yellow]")
            return

        stats = self._query_engine.auto_compactor.get_stats()
        lines = [
            "[bold]Token Usage Statistics:[/bold]",
            f"  Total tokens consumed: {stats.total_tokens}",
            f"  Peak tokens: {stats.peak_tokens}",
            f"  Avg tokens/turn: {stats.avg_tokens_per_turn:.1f}",
            f"  Compression count: {stats.compression_count}",
            f"  Current threshold: {self._query_engine.auto_compactor._dynamic_threshold:.2f}",
        ]
        self.add_assistant_message("\n".join(lines))

    async def _handle_user_message(self, message: str) -> None:
        """Process user message with QueryEngine event loop."""
        self.setup_status = get_setup_status()
        if not self.setup_status.overall_ready:
            self.add_assistant_message(self._get_setup_required_text())
            return
        if self._query_engine is None:
            self.add_assistant_message(
                "[red]Error: No LLM provider configured.[/red]\n"
                "Set ZHIPU_API_KEY environment variable and restart."
            )
            return

        self.update_current_response("Thinking...")
        self._activity_state["status"] = "thinking"
        self._activity_state["detail"] = "正在等待模型响应"
        self._refresh_side_panel()
        self._turn_count += 1
        self._update_header()

        await self._process_event_stream(self._query_engine.submit_message(message))

    async def _process_event_stream(
        self, stream: Any
    ) -> None:
        """Process a stream of events from QueryEngine."""
        full_response = ""

        try:
            async for event in stream:
                if isinstance(event, AssistantTextDelta):
                    full_response += event.text
                    self.update_current_response(full_response)

                elif isinstance(event, ToolExecutionStarted):
                    self.update_current_response("")
                    self.add_tool_call(
                        event.tool_name,
                        event.arguments,
                        tool_use_id=event.tool_use_id,
                    )

                elif isinstance(event, ToolExecutionCompleted):
                    self.add_tool_result(event.result, event.is_error)

                elif isinstance(event, AssistantTurnComplete):
                    self.update_current_response("")
                    if full_response:
                        self.add_assistant_message(full_response)
                    full_response = ""

                elif isinstance(event, PermissionRequestEvent):
                    self.update_current_response("")
                    self._activity_state.update(
                        {
                            "status": "approval",
                            "tool_name": event.tool_name,
                            "tool_use_id": event.tool_use_id,
                            "detail": event.reason,
                        }
                    )
                    self._refresh_side_panel()
                    await self._handle_permission_request(event)
                    return

                elif isinstance(event, PermissionResultEvent):
                    status = "approved" if event.approved else "denied"
                    self.add_assistant_message(
                        f"[yellow]Permission {status}: {event.reason}[/yellow]"
                    )

                elif isinstance(event, ErrorEvent):
                    self.update_current_response("")
                    self.add_assistant_message(
                        f"[red]Error: {type(event.error).__name__}: {event.error}[/red]"
                    )
                    if not event.recoverable:
                        return

        except Exception as e:
            self.update_current_response("")
            self.add_assistant_message(f"[red]Error: {type(e).__name__}: {e}[/red]")

    async def _handle_permission_request(self, event: PermissionRequestEvent) -> None:
        """Show permission modal and continue with user response."""
        def on_result(approved: bool) -> None:
            self.run_worker(self._continue_after_permission(event, approved))

        self.push_screen(
            PermissionModalScreen(
                tool_name=event.tool_name,
                arguments=event.arguments,
                reason=event.reason,
            ),
            callback=on_result,
        )

    async def _continue_after_permission(
        self, event: PermissionRequestEvent, approved: bool
    ) -> None:
        """Continue processing after user grants or denies permission."""
        tool_use_id = ""
        for msg in reversed(self._query_engine.messages):
            if msg.role == "assistant":
                for block in msg.content:
                    if hasattr(block, "name") and block.name == event.tool_name:
                        tool_use_id = block.id
                        break
                if tool_use_id:
                    break

        if not tool_use_id:
            self.add_assistant_message("[red]Error: Could not find tool use to resume.[/red]")
            return

        stream = self._query_engine.continue_with_permission(tool_use_id, approved)
        await self._process_event_stream(stream)

    def _switch_agent(self, agent_name: str) -> None:
        """Switch to a different agent."""
        if agent_name not in self._agents:
            available = ", ".join(self._agents.keys())
            self.add_assistant_message(f"Unknown agent '{agent_name}'. Available: {available}")
            return

        agent_def = self._agents[agent_name]
        self._current_agent_def = agent_def
        self.current_agent = agent_name
        self._config["agent"] = agent_name
        self._save_config()

        if self._query_engine is not None:
            tool_names = agent_def.tools
            if tool_names is not None:
                new_registry = _create_tool_registry(tool_names)
            else:
                disallowed = agent_def.disallowed_tools or []
                allowed = ["Read", "Bash", "Edit", "Write", "Glob", "Grep"]
                allowed = [t for t in allowed if t not in disallowed]
                new_registry = _create_tool_registry(allowed)

            permission_mode = agent_def.permission_mode or "default"
            if permission_mode == "dontAsk":
                new_checker = PermissionChecker()
                new_checker.approve_once("*", {})
            else:
                new_checker = PermissionChecker()

            self._query_engine.reconfigure(
                system_prompt=agent_def.system_prompt or "You are a helpful assistant.",
                tool_registry=new_registry,
                max_turns=agent_def.max_turns or 50,
                permission_checker=new_checker,
            )

        self._turn_count = 0
        self._update_header()
        tools = (
            ", ".join(t.name for t in self._query_engine.tool_registry.list_tools())
            if self._query_engine is not None
            else "未加载"
        )
        self.add_assistant_message(
            f"Switched to agent: {agent_name}\n"
            f"[dim]Tools: {tools}[/dim]"
        )

    def _switch_model(self, model_name: str) -> None:
        """Switch to a different model."""
        if self._provider is None:
            self.add_assistant_message("[red]Error: No provider configured.[/red]")
            return

        self._provider.model = model_name
        self.current_provider = f"zhipu/{model_name}"
        self.current_model = model_name
        self._config["model"] = model_name
        self._save_config()
        self._update_header()
        self.add_assistant_message(f"Switched to model: {model_name}")

    def _show_memory(self) -> None:
        """Show memory entries."""
        entries = self._memory_manager.list_memories()
        if not entries:
            self.add_assistant_message("No memory entries yet.")
            return

        lines = ["[bold]Memory Entries:[/bold]"]
        for entry in entries:
            lines.append(f"  - {entry.name}")
        self.add_assistant_message("\n".join(lines))

    def _load_config(self) -> None:
        """Load configuration from file."""
        if self._config_path.exists():
            try:
                with open(self._config_path, encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception:
                self._config = {}
        else:
            self._config = {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception:
            pass

    def _update_header(self) -> None:
        """Update header text."""
        cost = (
            f"${self._cost_tracker.total_cost:.4f}"
            if self._cost_tracker.total_cost > 0
            else "$0.0000"
        )
        header_text = (
            "MyAgent Workbench v0.2.0 | "
            f"Agent: {self.current_agent} | Model: {self.current_model} | "
            f"Turns: {self._turn_count} | Task: {self._task_status['state']} | "
            f"Cost: {cost} | Provider: {self.current_provider}"
        )
        try:
            header = self.query_one("#header", Static)
            header.update(header_text)
        except Exception:
            pass
        self._refresh_side_panel()

    def add_user_message(self, message: str) -> None:
        """Add a user message to the transcript."""
        self._add_line(f"[bold blue]You:[/bold blue] {message}")

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the transcript."""
        self._add_line(f"[bold green]Agent:[/bold green] {message}")

    def add_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        tool_use_id: str = "-",
    ) -> None:
        """Add a tool call to the transcript with formatted display."""
        args_lines = "\n".join(f"    [dim]{k}:[/dim] {v}" for k, v in arguments.items())
        self._activity_state.update(
            {
                "status": "running",
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "detail": args_lines or "无参数",
            }
        )
        self._refresh_side_panel()
        self._add_line(
            f"[bold yellow]╭─ Tool: {tool_name} [{tool_use_id}] ─╮[/bold yellow]\n"
            f"{args_lines}\n"
            f"[bold yellow]╰───────────────────╯[/bold yellow]"
        )

    def add_tool_result(self, result: str, is_error: bool = False) -> None:
        """Add a tool result to the transcript with formatted display."""
        prefix = (
            "[bold red]Error:[/bold red]"
            if is_error
            else "[bold cyan]Result:[/bold cyan]"
        )
        self._activity_state["status"] = "error" if is_error else "completed"
        self._activity_state["detail"] = result[:160] if result else "无输出"
        self._refresh_side_panel()

        preview = result[:500] + "..." if len(result) > 500 else result
        lines = preview.split("\n")
        if len(lines) > 10:
            preview = "\n".join(lines[:10]) + "\n..."

        self._add_line(f"{prefix}\n    {preview.replace(chr(10), chr(10) + '    ')}")

    def update_current_response(self, text: str) -> None:
        """Update the current response display."""
        self._current_response_text = text
        try:
            response_widget = self.query_one("#current-response", Static)
            response_widget.update(Text(text))
        except Exception:
            pass
        self._refresh_side_panel()

    def clear_transcript(self) -> None:
        """Clear the transcript and conversation history."""
        self._transcript_lines = []
        self._conversation_history = []
        if self._query_engine is not None:
            self._query_engine.messages = [
                ConversationMessage.from_system_text(self._query_engine.system_prompt)
            ]
        self._turn_count = 0
        try:
            transcript = self.query_one("#transcript", RichLog)
            transcript.clear()
        except Exception:
            pass

    def _add_line(self, line: str) -> None:
        """Add a line to the transcript."""
        self._transcript_lines.append(line)
        try:
            transcript = self.query_one("#transcript", RichLog)
            transcript.write(line)
        except Exception:
            pass

    def action_clear(self) -> None:
        """Clear the transcript via keyboard shortcut."""
        self.clear_transcript()

    def action_command_palette(self) -> None:
        """Open the command palette."""
        self.push_screen(
            CommandPaletteScreen(),
            callback=self._handle_palette_selection,
        )

    def _get_help_text(self) -> str:
        """Get help text for commands."""
        return """Available commands:
  /exit, /quit  - Exit MyAgent
  /clear        - Clear the transcript
  /help         - Show this help message
  /agent <name> - Switch to a different agent
  /provider <n> - Switch LLM provider
  /model <name> - Switch LLM model (e.g., glm-4.7, glm-5.1)
  /memory       - Show memory entries
  /setup        - Show setup required guidance
  /doctor       - Show setup health summary
  /tokens       - Show token usage statistics

Keyboard shortcuts:
  Enter      - Send message
  Shift+Enter - New line in message
  Ctrl+L     - Clear transcript
  Ctrl+R     - Regenerate last response
  Ctrl+D     - Exit"""

    def _get_setup_required_text(self) -> str:
        """Render setup guidance in the transcript."""
        issues = "\n".join(
            f"- {issue.summary} -> {issue.fix}"
            for issue in self.setup_status.issues
        )
        if not issues:
            issues = "- 当前配置尚未完成，请先运行初始化。"
        return (
            "[bold yellow]Setup Required[/bold yellow]\n"
            f"MyAgent Home: {self.setup_status.home}\n"
            f"Next: {self.setup_status.next_action}\n"
            f"{issues}"
        )

    def _get_session_summary(self) -> str:
        """Build the current session summary for modal display."""
        return (
            f"Agent: {self.current_agent}\n"
            f"Model: {self.current_model}\n"
            f"Provider: {self.current_provider}\n"
            f"Workspace: {self._workspace_path}\n"
            f"Turns: {self._turn_count}\n"
            f"Task: {self._task_status['state']}"
        )

    def _open_info_modal(self, title: str, body: str) -> None:
        """Show a simple informational modal."""
        self.push_screen(InfoModalScreen(title=title, body=body))

    def _handle_palette_selection(self, command: str | None) -> None:
        """Run the selected command from the command palette."""
        if not command:
            return
        if command == "/plan":
            self._open_info_modal("Plan", "使用 `/plan <任务描述>` 开始规划。")
            return
        self._handle_command(command)

    def _start_plan_flow(self, request: str) -> None:
        """Record a lightweight plan task and switch to the planner agent."""
        self._task_status = {
            "state": "planning",
            "request": request,
            "detail": "已切换到 plan agent，等待生成计划。",
        }
        self._switch_agent("plan")
        self._refresh_side_panel()
        self.add_assistant_message(
            "已进入规划模式。\n"
            f"[dim]Task: {request}[/dim]"
        )

    def apply_task_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Apply a task snapshot so TUI can mirror the current workflow state."""
        subtasks = snapshot.get("subtasks", [])
        completed = sum(1 for item in subtasks if item.get("status") == "done")
        total = len(subtasks)
        agents = sorted(
            {
                str(item.get("agent")).strip()
                for item in subtasks
                if item.get("agent")
            }
        )
        latest_event = "-"
        if snapshot.get("events"):
            latest_event = snapshot["events"][-1].get("message", "-")
        review_summary = "-"
        if snapshot.get("result"):
            review_summary = snapshot["result"].get("summary") or "-"

        detail_lines = [
            f"Progress: {completed}/{total}",
            f"Agents: {', '.join(agents) if agents else '-'}",
            f"Timeline: {latest_event}",
            f"Review: {review_summary}",
        ]
        self._task_status = {
            "state": snapshot.get("status", "idle"),
            "request": snapshot.get("title")
            or snapshot.get("description")
            or "",
            "detail": "\n".join(detail_lines),
        }
        self._update_header()

    def _refresh_side_panel(self) -> None:
        """Refresh the structured side panel widgets."""
        status_text = (
            f"Agent: {self.current_agent}\n"
            f"Model: {self.current_model}\n"
            f"Workspace: {self._workspace_path}\n"
            f"Setup: {'ready' if self.setup_status.overall_ready else 'required'}"
        )
        task_text = (
            f"State: {self._task_status['state']}\n"
            f"Request: {self._task_status['request'] or '-'}\n"
            f"Detail: {self._task_status['detail']}"
        )
        activity_text = (
            f"Status: {self._activity_state['status']}\n"
            f"Tool: {self._activity_state['tool_name']}\n"
            f"Use ID: {self._activity_state['tool_use_id']}\n"
            f"Detail: {self._activity_state['detail']}"
        )
        for widget_id, value in {
            "#status-panel": status_text,
            "#task-panel": task_text,
            "#activity-panel": activity_text,
        }.items():
            try:
                self.query_one(widget_id, Static).update(value)
            except Exception:
                continue


def run_tui() -> None:
    """Run the MyAgent TUI application."""
    app = MyAgentApp()
    app.run()
