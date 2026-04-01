from textual.app import App, ComposeResult

from ui.widgets import InputTextArea, OutputTextArea


class PiyApp(App[None]):
    """Root Textual application for piy."""

    TITLE = "piy"
    CSS_PATH = "app.tcss"

    def __init__(self) -> None:
        super().__init__()
        self._output_history = ""

    def on_mount(self) -> None:
        """Focus the input area when the app starts."""

        self.query_one(InputTextArea).focus()

    def on_input_text_area_submitted(self, event: InputTextArea.Submitted) -> None:
        """Handle prompt submission from the input widget."""

        self._append_prompt_to_history(event.text)
        self._clear_input()

    def compose(self) -> ComposeResult:
        """Compose the MVP UI shell."""

        yield OutputTextArea()
        yield InputTextArea()

    def _append_prompt_to_history(self, prompt: str) -> None:
        if self._output_history:
            self._output_history += "\n\n"

        self._output_history += prompt
        self._sync_output()

    def _sync_output(self) -> None:
        output = self.query_one(OutputTextArea)
        output.load_text(self._output_history)
        output.refresh()

    def _clear_input(self) -> None:
        self.query_one(InputTextArea).clear()
