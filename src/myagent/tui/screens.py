"""TUI screens for MyAgent."""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class PermissionModalScreen(ModalScreen[bool]):
    """Modal screen for permission approval."""

    CSS = """
    PermissionModalScreen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $warning;
    }

    #reason {
        color: $text-muted;
        text-align: center;
        margin: 1 0;
    }

    #details {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }

    #buttons {
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        tool_name: str,
        arguments: dict[str, str],
        reason: str,
    ) -> None:
        super().__init__()
        self.tool_name = tool_name
        self.arguments = arguments
        self.reason = reason

    def compose(self) -> ComposeResult:
        """Compose the permission dialog."""
        with Vertical(id="dialog"):
            yield Static("Permission Required", id="title")
            yield Static(self.reason, id="reason")

            details = f"Tool: {self.tool_name}\n"
            for key, value in self.arguments.items():
                details += f"{key}: {value}\n"
            yield Static(details.strip(), id="details")

            with Horizontal(id="buttons"):
                yield Button("Allow", id="allow", variant="success")
                yield Button("Deny", id="deny", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "allow":
            self.dismiss(True)
        else:
            self.dismiss(False)


class InfoModalScreen(ModalScreen[None]):
    """Simple informational modal used by setup/help/session handoff."""

    CSS = """
    InfoModalScreen {
        align: center middle;
    }

    #info-dialog {
        width: 72;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #info-title {
        text-style: bold;
        color: $accent;
    }

    #info-body {
        margin: 1 0;
        color: $text-muted;
    }

    #info-actions {
        align: right middle;
    }
    """

    def __init__(self, title: str, body: str) -> None:
        super().__init__()
        self.title_text = title
        self.body = body

    def compose(self) -> ComposeResult:
        """Compose the info dialog."""
        with Vertical(id="info-dialog"):
            yield Static(self.title_text, id="info-title")
            yield Static(self.body, id="info-body")
            with Horizontal(id="info-actions"):
                yield Button("Close", id="close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the info modal."""
        self.dismiss(None)


class CommandPaletteScreen(ModalScreen[str | None]):
    """Command palette for keyboard-driven high-frequency actions."""

    command_items: ClassVar[list[dict[str, str]]] = [
        {"command": "/help", "description": "查看帮助与快捷键"},
        {"command": "/setup", "description": "查看初始化与修复建议"},
        {"command": "/session", "description": "查看当前会话摘要"},
        {"command": "/plan", "description": "切换到规划模式并记录任务"},
        {"command": "/memory", "description": "查看当前记忆摘要"},
    ]

    CSS = """
    CommandPaletteScreen {
        align: center middle;
    }

    #palette-dialog {
        width: 68;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    .palette-item {
        width: 100%;
        margin: 0 0 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the palette items."""
        with Vertical(id="palette-dialog"):
            yield Static("Command Palette", id="palette-title")
            for item in self.command_items:
                yield Button(
                    f"{item['command']}  {item['description']}",
                    id=f"cmd-{item['command'][1:]}",
                    classes="palette-item",
                )
            yield Button("Cancel", id="cmd-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Return the selected command."""
        if event.button.id == "cmd-cancel":
            self.dismiss(None)
            return
        label = event.button.label.plain
        command = label.split()[0]
        self.dismiss(command)
