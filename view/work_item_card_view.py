import tkinter as tk

TYPE_LABELS = {
    "epic": "EPIC",
    "task": "TASK",
    "child_task": "SUB",
}

TYPE_COLORS = {
    "epic": "#7C3AED",
    "task": "#2563EB",
    "child_task": "#059669",
}


class WorkItemCardView(tk.Frame):
    def __init__(self, parent, item, on_click):
        """Build a card widget displaying the item's type badge, title, description, and due date."""
        super().__init__(
            parent,
            bg="#FFFFFF",
            relief="flat",
            bd=0,
            highlightbackground="#E2E8F0",
            highlightthickness=1,
            cursor="hand2",
        )
        self._item_id  = item.id
        self._on_click = on_click

        badge_color = TYPE_COLORS.get(item.type, "#64748B")
        badge_label = TYPE_LABELS.get(item.type, item.type.upper())

        badge = tk.Label(
            self,
            text=badge_label,
            bg=badge_color,
            fg="#FFFFFF",
            font=("Helvetica", 8, "bold"),
            padx=6,
            pady=2,
        )
        badge.pack(anchor="w", padx=8, pady=(8, 4))

        title = tk.Label(
            self,
            text=item.title,
            bg="#FFFFFF",
            fg="#1E293B",
            font=("Helvetica", 11, "bold"),
            anchor="w",
            wraplength=180,
            justify="left",
        )
        title.pack(anchor="w", padx=8)

        if item.description:
            short_desc = item.description[:80]
            if len(item.description) > 80:
                short_desc = short_desc + "…"
            desc = tk.Label(
                self,
                text=short_desc,
                bg="#FFFFFF",
                fg="#64748B",
                font=("Helvetica", 9),
                anchor="w",
                wraplength=180,
                justify="left",
            )
            desc.pack(anchor="w", padx=8, pady=(2, 0))

        if item.due_date:
            due = tk.Label(
                self,
                text=f"Due {item.due_date.isoformat()}",
                bg="#FFFFFF",
                fg="#94A3B8",
                font=("Helvetica", 8),
                anchor="w",
            )
            due.pack(anchor="w", padx=8, pady=(4, 0))

        tk.Frame(self, height=8, bg="#FFFFFF").pack()

        # Bind click on the card frame and every child widget inside it.
        for widget in self.winfo_children():
            widget.bind("<Button-1>", self._on_click_event)
        self.bind("<Button-1>", self._on_click_event)

    def _on_click_event(self, event):
        """Fire the on_click callback with this card's item id."""
        self._on_click(self._item_id)
