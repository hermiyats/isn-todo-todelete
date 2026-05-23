import tkinter as tk
import re

BG       = "#1E293B"
BG_FIELD = "#0F172A"
FG       = "#F1F5F9"
FG_DIM   = "#94A3B8"
ACCENT   = "#3B82F6"
RED      = "#EF4444"
F_NORM   = ("Helvetica", 11)
F_BOLD   = ("Helvetica", 11, "bold")
F_SM     = ("Helvetica", 9)

PRESET_COLORS = [
    "#64748B",  # slate
    "#EF4444",  # red
    "#F97316",  # orange
    "#EAB308",  # yellow
    "#22C55E",  # green
    "#14B8A6",  # teal
    "#3B82F6",  # blue
    "#8B5CF6",  # violet
    "#EC4899",  # pink
    "#6B7280",  # gray
]

HEX_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')


class StatusDialog(tk.Toplevel):
    def __init__(self, parent, controller):
        """Open the Add Status dialog."""
        super().__init__(parent)
        self._controller = controller

        self.title("Add Status")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        self._selected_color = tk.StringVar(value=PRESET_COLORS[0])
        self._build()

        self.update_idletasks()
        self.geometry("400x320")

    # ── build ─────────────────────────────────────────────────────────

    def _build(self):
        """Construct the name field, color swatches, hex input, and submit button."""
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        # Name ────────────────────────────────────────────────────────
        tk.Label(outer, text="Status name *", bg=BG, fg=FG_DIM, font=F_SM).pack(anchor="w")
        self._name_var = tk.StringVar()
        tk.Entry(outer, textvariable=self._name_var, bg=BG_FIELD, fg=FG,
                 font=F_NORM, relief="flat", insertbackground=FG).pack(
                     fill="x", pady=(4, 16), ipady=4)

        # Color swatches ──────────────────────────────────────────────
        tk.Label(outer, text="Color", bg=BG, fg=FG_DIM, font=F_SM).pack(anchor="w")
        swatch_row = tk.Frame(outer, bg=BG)
        swatch_row.pack(anchor="w", pady=(4, 8))

        self._swatches = []
        for color in PRESET_COLORS:
            s = tk.Label(swatch_row, bg=color, width=2, height=1, cursor="hand2",
                         relief="flat")
            s.pack(side="left", padx=2)
            s.bind("<Button-1>", lambda e, c=color: self._select_color(c))
            self._swatches.append((color, s))

        # Hex input ───────────────────────────────────────────────────
        hex_row = tk.Frame(outer, bg=BG)
        hex_row.pack(fill="x", pady=(0, 4))
        tk.Label(hex_row, text="#", bg=BG, fg=FG_DIM, font=F_NORM).pack(side="left")
        self._hex_var = tk.StringVar(value=PRESET_COLORS[0].lstrip("#"))
        hex_entry = tk.Entry(hex_row, textvariable=self._hex_var, bg=BG_FIELD, fg=FG,
                             font=F_NORM, relief="flat", insertbackground=FG, width=8)
        hex_entry.pack(side="left", padx=(4, 8), ipady=4)

        self._preview = tk.Label(hex_row, bg=PRESET_COLORS[0], width=3, height=1)
        self._preview.pack(side="left")

        self._hex_var.trace_add("write", self._on_hex_change)

        self._select_color(PRESET_COLORS[0])

        # Error + Add button ──────────────────────────────────────────
        self._error_var = tk.StringVar()
        tk.Label(outer, textvariable=self._error_var, bg=BG, fg=RED,
                 font=F_SM).pack(anchor="w", pady=(8, 0))

        add_btn = tk.Label(outer, text="Add Status", bg=ACCENT, fg=FG,
                           font=F_BOLD, padx=12, pady=6, cursor="hand2")
        add_btn.pack(anchor="e", pady=(8, 0))
        add_btn.bind("<Button-1>", lambda e: self._on_add())

    # ── color logic ───────────────────────────────────────────────────

    def _select_color(self, color):
        """Set the active color, sync the hex field, preview, and swatch highlights."""
        self._selected_color.set(color)
        self._hex_var.set(color.lstrip("#"))
        self._preview.config(bg=color)
        for c, swatch in self._swatches:
            if c == color:
                swatch.config(relief="sunken", bd=2)
            else:
                swatch.config(relief="flat", bd=0)

    def _on_hex_change(self, *_):
        """Update the preview when the user types a valid hex color."""
        raw = self._hex_var.get().strip()
        hex_color = f"#{raw}"
        if HEX_RE.match(hex_color):
            self._selected_color.set(hex_color)
            self._preview.config(bg=hex_color)
            self._error_var.set("")
        else:
            self._preview.config(bg=BG_FIELD)

    # ── add ───────────────────────────────────────────────────────────

    def _on_add(self):
        """Validate the form and delegate status creation to the controller."""
        name = self._name_var.get().strip()
        if not name:
            self._error_var.set("Status name is required.")
            return

        hex_color = f"#{self._hex_var.get().strip()}"
        if not HEX_RE.match(hex_color):
            self._error_var.set("Invalid hex color — use format #RRGGBB.")
            return

        try:
            self._controller.add_status(name, hex_color)
        except ValueError as e:
            self._error_var.set(str(e))
            return

        self._name_var.set("")
        self._select_color(PRESET_COLORS[0])
        self._error_var.set(f"✓ '{name}' added.")
