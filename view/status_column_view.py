import tkinter as tk
from view.work_item_card_view import WorkItemCardView

BG_NORMAL = "#F1F5F9"


class StatusColumnView(tk.Frame):
    def __init__(self, parent, status, items,
                 on_card_click, on_delete_status,
                 on_move_left=None, on_move_right=None):
        """Build a column for one status, including a header bar and a scrollable card list."""
        super().__init__(parent, bg=BG_NORMAL, relief="flat")

        self.status_id = status.id

        # ── colored top bar ──────────────────────────────────────────
        tk.Frame(self, bg=status.color, height=6).pack(fill="x")

        label_row = tk.Frame(self, bg=BG_NORMAL)
        label_row.pack(fill="x", padx=12, pady=(10, 6))

        if on_move_left:
            arrow_l = tk.Label(label_row, text="←", bg=BG_NORMAL, fg="#94A3B8",
                               font=("Helvetica", 11), cursor="hand2")
            arrow_l.pack(side="left", padx=(0, 4))
            arrow_l.bind("<Button-1>", lambda e: on_move_left(status.id))
            arrow_l.bind("<Enter>", lambda e: arrow_l.config(fg="#475569"))
            arrow_l.bind("<Leave>", lambda e: arrow_l.config(fg="#94A3B8"))

        tk.Label(
            label_row,
            text=status.label.upper(),
            bg=BG_NORMAL,
            fg="#475569",
            font=("Helvetica", 10, "bold"),
            anchor="w",
        ).pack(side="left")

        if on_move_right:
            arrow_r = tk.Label(label_row, text="→", bg=BG_NORMAL, fg="#94A3B8",
                               font=("Helvetica", 11), cursor="hand2")
            arrow_r.pack(side="left", padx=(4, 0))
            arrow_r.bind("<Button-1>", lambda e: on_move_right(status.id))
            arrow_r.bind("<Enter>", lambda e: arrow_r.config(fg="#475569"))
            arrow_r.bind("<Leave>", lambda e: arrow_r.config(fg="#94A3B8"))

        delete_btn = tk.Label(
            label_row,
            text="✕",
            bg=BG_NORMAL,
            fg="#EF4444",
            font=("Helvetica", 11, "bold"),
            cursor="hand2",
        )
        delete_btn.pack(side="right", padx=(4, 0))
        delete_btn.bind("<Button-1>", lambda e: on_delete_status(status.id))

        tk.Label(
            label_row,
            text=str(len(items)),
            bg="#CBD5E1",
            fg="#475569",
            font=("Helvetica", 9, "bold"),
            padx=6,
            pady=1,
        ).pack(side="right")

        # ── scrollable card list ─────────────────────────────────────
        canvas = tk.Canvas(self, bg=BG_NORMAL, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        card_container = tk.Frame(canvas, bg=BG_NORMAL)
        container_id = canvas.create_window((0, 0), window=card_container, anchor="nw")

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(container_id, width=e.width))
        card_container.bind("<Configure>",
                            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        for item in items:
            card = WorkItemCardView(card_container, item, on_click=on_card_click)
            card.pack(fill="x", padx=8, pady=4)
