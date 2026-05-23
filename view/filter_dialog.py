import tkinter as tk


class FilterDialog(tk.Toplevel):
    def __init__(self, parent, on_apply):
        """Modal for entering a WIQL filter query."""
        super().__init__(parent)
        self._on_apply = on_apply

        self.title("Filter (WIQL)")
        self.resizable(False, False)
        self.configure(bg="#1E293B")
        self.grab_set()

        self._build()
        self._center(parent)

    def _build(self):
        tk.Label(
            self, text="WIQL Filter",
            bg="#1E293B", fg="#F8FAFC",
            font=("Helvetica", 13, "bold"),
        ).pack(padx=20, pady=(16, 4))

        tk.Label(
            self,
            text="Example:  FROM * SELECT * WHERE title ~= 'bug'",
            bg="#1E293B", fg="#64748B",
            font=("Courier", 9),
        ).pack(padx=20, pady=(0, 12))

        self._var = tk.StringVar()
        self._var.trace_add("write", self._on_text_change)

        self._entry = tk.Entry(
            self,
            textvariable=self._var,
            bg="#0F172A", fg="#F8FAFC",
            insertbackground="#F8FAFC",
            font=("Courier", 11),
            relief="flat",
            width=50,
        )
        self._entry.pack(padx=20, pady=(0, 16), ipady=6)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda e: self._apply())

        btn_frame = tk.Frame(self, bg="#1E293B")
        btn_frame.pack(padx=20, pady=(0, 16), fill="x")

        self._close_btn = tk.Label(
            btn_frame, text="Close",
            bg="#334155", fg="#94A3B8",
            font=("Helvetica", 10),
            padx=12, pady=6, cursor="hand2",
        )
        self._close_btn.pack(side="left")
        self._close_btn.bind("<Button-1>", lambda e: self.destroy())

        self._filter_btn = tk.Label(
            btn_frame, text="Apply Filter",
            font=("Helvetica", 10, "bold"),
            padx=12, pady=6,
        )
        self._filter_btn.pack(side="right")
        self._set_filter_btn_enabled(False)

    def _on_text_change(self, *_):
        self._set_filter_btn_enabled(bool(self._var.get().strip()))

    def _set_filter_btn_enabled(self, enabled: bool):
        if enabled:
            self._filter_btn.config(bg="#3B82F6", fg="#FFFFFF", cursor="hand2")
            self._filter_btn.bind("<Button-1>", lambda e: self._apply())
        else:
            self._filter_btn.config(bg="#1E3A5F", fg="#64748B", cursor="arrow")
            self._filter_btn.unbind("<Button-1>")

    def _apply(self):
        query = self._var.get().strip()
        if query:
            self._on_apply(query)
            self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
