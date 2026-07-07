"""Modal screens: add-package flow, diff/apply, confirm, new module."""

from __future__ import annotations

from pathlib import Path

from rich.syntax import Syntax
from rich.text import Text
from textual import work
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Label,
    LoadingIndicator,
    Select,
    Static,
)

from ..core import search
from ..core.edits import EditPlan
from ..core.pipeline import ApplyResult, Pipeline
from ..core.search import SearchResult


class ConfirmScreen(ModalScreen[bool]):
    """Simple Yes/No confirmation."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(False)

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    ConfirmScreen > Vertical {
        width: 60;
        height: auto;
        border: round $warning;
        padding: 1 2;
        background: $surface;
    }
    ConfirmScreen #confirm-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self):
        with Vertical():
            yield Static(self.message, id="confirm-message", markup=False)
            with Horizontal(id="confirm-buttons"):
                yield Button("No", id="no")
                yield Button("Yes", id="yes", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class DiffScreen(ModalScreen[ApplyResult | None]):
    """Shows a plan's diff; Apply runs the pipeline in a worker thread."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        if not self._applying:  # can't abandon a write in flight
            self.dismiss(None)

    DEFAULT_CSS = """
    DiffScreen {
        align: center middle;
    }
    DiffScreen > Vertical {
        width: 90%;
        height: 90%;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    DiffScreen #diff-title {
        text-style: bold;
        margin-bottom: 1;
    }
    DiffScreen #diff-scroll {
        height: 1fr;
        border: solid $panel;
    }
    DiffScreen #diff-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    DiffScreen #diff-loading {
        height: 1;
        margin-top: 1;
    }
    """

    def __init__(self, pipeline: Pipeline, plan: EditPlan) -> None:
        super().__init__()
        self.pipeline = pipeline
        self.plan = plan
        self._applying = False

    def compose(self):
        diff_text = self.plan.diff() or "(no changes)"
        with Vertical():
            yield Static(self.plan.description, id="diff-title", markup=False)
            with VerticalScroll(id="diff-scroll"):
                yield Static(Syntax(diff_text, "diff", word_wrap=True), id="diff-body")
            yield LoadingIndicator(id="diff-loading")
            with Horizontal(id="diff-buttons"):
                yield Button("Cancel", id="cancel-btn")
                yield Button("Apply", id="apply-btn", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#diff-loading", LoadingIndicator).display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "apply-btn":
            self._applying = True
            self.query_one("#apply-btn", Button).disabled = True
            self.query_one("#cancel-btn", Button).disabled = True
            self.query_one("#diff-loading", LoadingIndicator).display = True
            self._apply()

    @work(thread=True)
    def _apply(self) -> None:
        result = self.pipeline.apply(self.plan)
        self.app.call_from_thread(self.dismiss, result)


class NewModuleScreen(ModalScreen[tuple[str, str] | None]):
    """Ask for a new module's relative path and description."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(None)

    DEFAULT_CSS = """
    NewModuleScreen {
        align: center middle;
    }
    NewModuleScreen > Vertical {
        width: 70;
        height: auto;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    NewModuleScreen #new-module-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    """

    def __init__(self, default_dir: str) -> None:
        super().__init__()
        self.default_dir = default_dir.rstrip("/")

    def compose(self):
        with Vertical():
            yield Static("New module", id="new-module-title")
            yield Label("File path (relative to config root)")
            yield Input(value=f"{self.default_dir}/", id="path-input")
            yield Label("Description")
            yield Input(id="desc-input")
            with Horizontal(id="new-module-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="create", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        path = self.query_one("#path-input", Input).value.strip()
        desc = self.query_one("#desc-input", Input).value.strip()
        if not path or not desc:
            self.app.notify("Path and description are required", severity="error")
            return
        if not path.endswith(".nix"):
            path += ".nix"
        self.dismiss((path, desc))


class CommentScreen(ModalScreen[str | None]):
    """Edit a package's inline comment. Dismisses with the new comment
    ("" clears it) or None on cancel."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(None)

    DEFAULT_CSS = """
    CommentScreen {
        align: center middle;
    }
    CommentScreen > Vertical {
        width: 70;
        height: auto;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    CommentScreen #comment-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    """

    def __init__(self, package_name: str, current: str) -> None:
        super().__init__()
        self.package_name = package_name
        self.current = current

    def compose(self):
        with Vertical():
            yield Static(
                f"Comment for {self.package_name}", id="comment-title", markup=False
            )
            yield Label("Leave empty to remove the comment")
            yield Input(value=self.current, id="comment-value")
            with Horizontal(id="comment-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#comment-value", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        else:
            self.dismiss(self.query_one("#comment-value", Input).value.strip())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())


HELP_TEXT = """\
 Navigation
   ↑/↓  or  j/k        move cursor
   →/←  or  l/h        expand / collapse (← on a leaf: jump to parent)
   g / G               top / bottom of tree
   Shift+↑/↓           previous / next sibling
   Shift+←             jump to parent
   /                   find in tree (Enter: next match, Esc: close)

 Editing
   a                   add package (search nixpkgs or type a name)
   Space               enable / disable package or module import
   c                   edit a package's inline comment
   d                   remove package (asks for confirmation)
   n                   new module under the highlighted module/branch
   u                   undo the last applied change (git revert)

 Other
   e                   open the highlighted file in $EDITOR at this line
   y                   copy the highlighted name to the clipboard
   v                   run `nix flake check` now
   r                   reload config from disk
   Ctrl+P              command palette (all actions, searchable)
   ?                   this help
   q                   quit

 In dialogs: Tab/Shift+Tab move focus, Enter submits, Esc cancels.
 Every edit shows its diff first; applying validates the flake and
 makes one git commit, so `u` (or `git revert`) undoes it cleanly.
"""


class HelpScreen(ModalScreen[None]):
    """Full keyboard reference."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("question_mark", "close", "Close"),
    ]

    def action_close(self) -> None:
        self.dismiss(None)

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > VerticalScroll {
        width: 76;
        height: 90%;
        max-height: 42;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    HelpScreen #help-title {
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def compose(self):
        with VerticalScroll():
            yield Static("nixcfg — keys", id="help-title")
            yield Static(HELP_TEXT)


class PickPackageScreen(ModalScreen[tuple[str, str] | None]):
    """Step 1 of add-package: search nixpkgs, or type an attr name directly."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(None)

    DEFAULT_CSS = """
    PickPackageScreen {
        align: center middle;
    }
    PickPackageScreen > Vertical {
        width: 90%;
        height: 90%;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    PickPackageScreen #pick-results {
        height: 1fr;
        margin-top: 1;
    }
    PickPackageScreen #pick-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    PickPackageScreen #pick-notice {
        color: $warning;
    }
    """

    def __init__(self, search_available: bool, flake_root: Path) -> None:
        super().__init__()
        self.search_available = search_available
        self.flake_root = flake_root
        self._results: list[SearchResult] = []

    def compose(self):
        with Vertical():
            yield Static("Add package", id="pick-title")
            if not self.search_available:
                yield Static(
                    "nix not found — type the exact attribute name",
                    id="pick-notice",
                )
            yield Input(
                placeholder="search query or attribute name", id="pick-query"
            )
            yield LoadingIndicator(id="pick-loading")
            yield DataTable(id="pick-results")
            with Horizontal(id="pick-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Use typed name", id="use-typed")
                if self.search_available:
                    yield Button("Search", id="search-btn", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#pick-results", DataTable)
        table.add_columns("attr", "version", "description")
        table.cursor_type = "row"
        self.query_one("#pick-loading", LoadingIndicator).display = False
        self.query_one("#pick-query", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "search-btn":
            self._run_search()
        elif event.button.id == "use-typed":
            self._use_typed()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.search_available:
            self._run_search()
        else:
            self._use_typed()

    def _use_typed(self) -> None:
        name = self.query_one("#pick-query", Input).value.strip()
        if not name:
            self.app.notify("Enter a package attribute name", severity="error")
            return
        self.dismiss((name, ""))

    def _run_search(self) -> None:
        query = self.query_one("#pick-query", Input).value.strip()
        if not query:
            return
        self.query_one("#pick-loading", LoadingIndicator).display = True
        self._do_search(query)

    @work(thread=True)
    def _do_search(self, query: str) -> None:
        try:
            results = search.search_nixpkgs(query, flake_root=self.flake_root)
        except RuntimeError as exc:
            self.app.call_from_thread(self._search_error, str(exc))
            return
        self.app.call_from_thread(self._search_done, results)

    def _search_error(self, message: str) -> None:
        self.query_one("#pick-loading", LoadingIndicator).display = False
        self.app.notify(message, severity="error")

    def _search_done(self, results: list[SearchResult]) -> None:
        self.query_one("#pick-loading", LoadingIndicator).display = False
        self._results = results
        table = self.query_one("#pick-results", DataTable)
        table.clear()
        for r in results:
            # Wrap as Text (not raw str): descriptions come from upstream
            # nixpkgs metadata and routinely contain '[' / ']', which
            # DataTable would otherwise try to parse as Rich markup.
            table.add_row(
                Text(r.attr),
                Text(r.version),
                Text(r.description),
                key=r.attr,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = event.row_key.value
        result = next((r for r in self._results if r.attr == key), None)
        if result is not None:
            self.dismiss((result.attr, result.description))


class PackageDetailsScreen(ModalScreen[tuple[str | None, str | None] | None]):
    """Step 2 of add-package: optional comment + section."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(None)

    NO_SECTION = "\0no-section"
    NEW_SECTION = "\0new-section"

    DEFAULT_CSS = """
    PackageDetailsScreen {
        align: center middle;
    }
    PackageDetailsScreen > Vertical {
        width: 70;
        height: auto;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    PackageDetailsScreen #details-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    """

    def __init__(
        self,
        attr: str,
        prefill_comment: str,
        section_titles: list[str],
        default_section: str | None,
    ) -> None:
        super().__init__()
        self.attr = attr
        self.prefill_comment = prefill_comment
        self.section_titles = section_titles
        self.default_section = default_section

    def compose(self):
        options = [(t, t) for t in self.section_titles]
        options.append(("(no section)", self.NO_SECTION))
        options.append(("(new section...)", self.NEW_SECTION))
        default_value = (
            self.default_section
            if self.default_section in self.section_titles
            else self.NO_SECTION
        )
        with Vertical():
            yield Static(f"Add {self.attr}", id="details-title", markup=False)
            yield Label("Comment (optional)")
            yield Input(value=self.prefill_comment, id="comment-input")
            yield Label("Section")
            yield Select(
                options,
                value=default_value,
                allow_blank=False,
                id="section-select",
            )
            yield Input(
                placeholder="new section title",
                id="new-section-input",
            )
            with Horizontal(id="details-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Add", id="add", variant="primary")

    def on_mount(self) -> None:
        self._sync_new_section_visibility()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "section-select":
            self._sync_new_section_visibility()

    def _sync_new_section_visibility(self) -> None:
        sel = self.query_one("#section-select", Select)
        new_input = self.query_one("#new-section-input", Input)
        new_input.display = sel.value == self.NEW_SECTION

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        self._submit()

    def _submit(self) -> None:
        comment = self.query_one("#comment-input", Input).value.strip() or None
        sel_value = self.query_one("#section-select", Select).value
        if sel_value == self.NEW_SECTION:
            section = self.query_one("#new-section-input", Input).value.strip()
            if not section:
                self.app.notify("Enter a section title", severity="error")
                return
        elif sel_value == self.NO_SECTION:
            section = None
        else:
            section = sel_value
        self.dismiss((comment, section))
