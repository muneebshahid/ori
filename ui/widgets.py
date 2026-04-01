from __future__ import annotations
from textual import events
from textual.message import Message
from textual.widgets import TextArea


class OutputTextArea(TextArea):
    """Read-only transcript area shown above the input."""

    can_focus = False

    def __init__(self) -> None:
        super().__init__(
            text="",
            id="output",
            read_only=True,
            show_cursor=False,
            placeholder="Welcome to Piy!",
        )


class InputTextArea(TextArea):
    """Editable prompt area shown below the output."""

    class Submitted(Message):
        """Message sent when the user submits the input area."""

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def __init__(self) -> None:
        super().__init__(
            text="",
            id="input",
        )

    def on_key(self, event: events.Key) -> None:
        """Convert Enter into a submit event instead of a newline."""

        if event.key != "enter":
            return

        event.prevent_default()
        event.stop()

        if not (prompt := self.text.strip()):
            return

        self.post_message(self.Submitted(prompt))
