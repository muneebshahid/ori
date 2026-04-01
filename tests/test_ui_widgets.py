import asyncio

from textual.app import App, ComposeResult

from ui.widgets import InputTextArea


class InputHarnessApp(App[None]):
    """Minimal app used to verify input widget behavior."""

    def __init__(self) -> None:
        super().__init__()
        self.submissions: list[str] = []

    def compose(self) -> ComposeResult:
        yield InputTextArea()

    def on_mount(self) -> None:
        self.query_one(InputTextArea).focus()

    def on_input_text_area_submitted(self, event: InputTextArea.Submitted) -> None:
        self.submissions.append(event.text)


def test_input_text_area_posts_submitted_message_on_enter() -> None:
    async def _run() -> None:
        app = InputHarnessApp()

        async with app.run_test() as pilot:
            input_area = app.query_one(InputTextArea)

            input_area.load_text("Hello from widget")
            await pilot.press("enter")
            await pilot.pause()

            assert app.submissions == ["Hello from widget"]

    asyncio.run(_run())
