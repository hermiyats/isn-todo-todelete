import tkinter as tk
from view.kanban_board_view import KanbanBoardView
from view.work_item_dialog import WorkItemDialog
from view.status_dialog import StatusDialog
from view.chart_window import ChartWindow


def _make_button(parent, text, bg, fg, font, command=None, disabled=False):
    """Label-based button — renders custom colors correctly on macOS."""
    actual_fg = fg if not disabled else "#64748B"
    actual_cursor = "hand2" if not disabled else "arrow"
    label = tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=actual_fg,
        font=font,
        padx=12,
        pady=6,
        cursor=actual_cursor,
    )
    if command and not disabled:
        label.bind("<Button-1>", lambda e: command())
        label.bind("<Enter>", lambda e: label.config(bg=_darken(bg)))
        label.bind("<Leave>", lambda e: label.config(bg=bg))
    return label


def _darken(hex_color):
    """Slightly darken a hex color for hover effect."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, r - 25)
    g = max(0, g - 25)
    b = max(0, b - 25)
    return f"#{r:02x}{g:02x}{b:02x}"


class MainWindow(tk.Tk):
    def __init__(self, controller):
        """Initialise the root window and wire it to the board controller."""
        super().__init__()
        self._controller = controller
        self._controller.subscribe(self.refresh)

        self.title("ISN Task Manager")
        self.geometry("1200x750")
        self.minsize(800, 500)
        self.configure(bg="#0F172A")

        self._build_header()
        self._build_board()
        self._build_footer()

        self.refresh()

    # ── layout ──────────────────────────────────────────────────────

    def _build_header(self):
        """Build the top bar with the app title and action buttons."""
        header = tk.Frame(self, bg="#1E293B", pady=10)
        header.pack(fill="x")

        tk.Label(
            header,
            text="ISN Task Manager",
            bg="#1E293B",
            fg="#F8FAFC",
            font=("Helvetica", 14, "bold"),
        ).pack(side="left", padx=16)

        action_buttons = [
            ("+ Epic",     self._on_new_epic),
            ("+ Task",     self._on_new_task),
            ("+ Sub-task", self._on_new_child_task),
        ]
        for text, cmd in action_buttons:
            _make_button(header, text, "#3B82F6", "#FFFFFF",
                         ("Helvetica", 10, "bold"), command=cmd).pack(side="left", padx=4)

        _make_button(header, "Filter (WIQL)", "#334155", "#94A3B8",
                     ("Helvetica", 10), disabled=True).pack(side="right", padx=4)

        _make_button(header, "Charts", "#0EA5E9", "#FFFFFF",
                     ("Helvetica", 10, "bold"),
                     command=self._on_show_charts).pack(side="right", padx=4)

        _make_button(header, "+ Status", "#0F172A", "#FFFFFF",
                     ("Helvetica", 10, "bold"), command=self._on_new_status).pack(side="right", padx=4)

    def _build_board(self):
        """Create and pack the main Kanban board view."""
        self._board_view = KanbanBoardView(self)
        self._board_view.pack(fill="both", expand=True, padx=6, pady=6)

    def _build_footer(self):
        """Build the status bar at the bottom of the window."""
        footer = tk.Frame(self, bg="#1E293B", pady=6)
        footer.pack(fill="x", side="bottom")

        self._footer_label = tk.Label(
            footer,
            text="Ready.",
            bg="#1E293B",
            fg="#94A3B8",
            font=("Helvetica", 9),
            anchor="w",
        )
        self._footer_label.pack(side="left", padx=16)

    # ── public ───────────────────────────────────────────────────────

    def refresh(self):
        """Redraw the board with the latest data from the controller."""
        self._board_view.refresh(
            self._controller.board,
            self._on_card_click,
            self._on_delete_status,
            on_move_left  = self._on_move_status_left,
            on_move_right = self._on_move_status_right,
        )

    def show_message(self, text, error=False):
        """Display a message in the footer status bar."""
        self._footer_label.config(
            text=text,
            fg="#F87171" if error else "#94A3B8",
        )

    # ── callbacks ────────────────────────────────────────────────────

    def _open_dialog(self, item_type, item=None, parent_id=None):
        """Open the work item dialog in create or edit mode."""
        WorkItemDialog(self, self._controller, item_type,
                       item=item, parent_id=parent_id)

    def _on_card_click(self, item_id):
        """Open the edit dialog for the clicked card."""
        item = self._controller.board.find_by_id(item_id)
        if item:
            self._open_dialog(item.type, item=item)

    def _on_new_epic(self):
        self._open_dialog("epic")

    def _on_new_task(self):
        self._open_dialog("task")

    def _on_new_child_task(self):
        self._open_dialog("child_task")

    def _on_move_status_left(self, status_id: str):
        self._controller.move_status_left(status_id)

    def _on_move_status_right(self, status_id: str):
        self._controller.move_status_right(status_id)

    def _on_new_status(self):
        StatusDialog(self, self._controller)

    def _on_show_charts(self):
        ChartWindow(self, self._controller.board)

    def _on_delete_status(self, status_id: str):
        """Delete a status column, showing an error if items block it."""
        try:
            self._controller.delete_status(status_id)
            self.show_message("Status deleted.")
        except ValueError as e:
            self.show_message(str(e), error=True)
