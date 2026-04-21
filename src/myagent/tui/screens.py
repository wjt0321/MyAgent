"""TUI screens for MyAgent."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


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
