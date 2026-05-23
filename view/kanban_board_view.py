import tkinter as tk
from view.status_column_view import StatusColumnView


class KanbanBoardView(tk.Frame):
    def __init__(self, parent):
        """Initialise the board frame."""
        super().__init__(parent, bg="#E2E8F0")
        self._columns: list[StatusColumnView] = []

    def refresh(self, board, on_card_click, on_delete_status,
                on_move_left=None, on_move_right=None):
        """Destroy and rebuild all status columns from the current board state."""
        for col in self._columns:
            col.destroy()
        self._columns = []

        statuses  = sorted(board.statuses, key=lambda s: s.order)
        all_items = board.all_items()

        for idx, status in enumerate(statuses):
            items = []
            for item in all_items:
                if item.status_id == status.id:
                    items.append(item)

            col = StatusColumnView(
                self, status, items,
                on_card_click    = on_card_click,
                on_delete_status = on_delete_status,
                on_move_left     = on_move_left  if idx > 0                   else None,
                on_move_right    = on_move_right if idx < len(statuses) - 1   else None,
            )
            col.grid(row=0, column=idx, sticky="nsew", padx=6, pady=6)
            self.grid_columnconfigure(idx, weight=1, uniform="col")
            self._columns.append(col)

        self.grid_rowconfigure(0, weight=1)
