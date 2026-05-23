import tkinter as tk
import tkinter.ttk as ttk
from datetime import date

# ── constants ────────────────────────────────────────────────────────────────

ITEM_LABELS  = {"epic": "Epic", "task": "Task", "child_task": "Sub-task"}
CHILD_TYPE   = {"epic": "task", "task": "child_task"}
CHILD_LABEL  = {"epic": "Tasks", "task": "Sub-tasks"}

BG       = "#1E293B"
BG_FIELD = "#0F172A"
BG_ROW   = "#0F172A"
FG       = "#F1F5F9"
FG_DIM   = "#94A3B8"
ACCENT   = "#3B82F6"
RED      = "#EF4444"
F_NORM   = ("Helvetica", 11)
F_BOLD   = ("Helvetica", 11, "bold")
F_SM     = ("Helvetica", 9)


# ── helpers ──────────────────────────────────────────────────────────────────

def _label(parent, text, font=F_SM, fg=FG_DIM):
    tk.Label(parent, text=text, bg=BG, fg=fg, font=font).pack(anchor="w")


def _entry(parent, var):
    e = tk.Entry(parent, textvariable=var, bg=BG_FIELD, fg=FG,
                 font=F_NORM, relief="flat", insertbackground=FG)
    e.pack(fill="x", pady=(4, 12), ipady=4)
    return e


def _btn(parent, text, command, bg=ACCENT):
    b = tk.Label(parent, text=text, bg=bg, fg=FG, font=F_BOLD,
                 padx=12, pady=6, cursor="hand2")
    b.bind("<Button-1>", lambda e: command())
    return b


# ── dialog ───────────────────────────────────────────────────────────────────

class WorkItemDialog(tk.Toplevel):
    """
    Dual-purpose modal:
      - Create mode  (item=None): form to fill in, parent selector for task/child_task
      - Edit mode    (item set):  pre-filled form + children list with add/remove
    Delegates all mutations to the BoardController.
    """

    def __init__(self, parent, controller, item_type, item=None, parent_id=None):
        """Open the dialog in create or edit mode depending on whether item is provided."""
        super().__init__(parent)
        self._controller = controller
        self._item_type  = item_type
        self._item       = item
        self._parent_id  = parent_id
        self._is_create  = item is None

        mode = "New" if self._is_create else "Edit"
        self.title(f"{mode} {ITEM_LABELS[item_type]}")
        self.configure(bg=BG)
        self.resizable(False, True)
        self.grab_set()
        self.transient(parent)

        self._build()
        if not self._is_create:
            self._populate()

        self.update_idletasks()
        self.geometry("520x640")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # ── build ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _setup_combobox_style():
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TCombobox",
            fieldbackground=BG_FIELD, background=BG_FIELD,
            foreground=FG, selectbackground=ACCENT, selectforeground=FG,
            arrowcolor=FG, arrowsize=14, borderwidth=0, relief="flat",
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", BG_FIELD), ("focus", BG_FIELD)],
            background=[("readonly", BG_FIELD), ("active", "#334155")],
            foreground=[("readonly", FG)],
            arrowcolor=[("readonly", FG), ("active", FG)],
        )

    def _build(self):
        self._setup_combobox_style()
        """Construct all form fields and lay them out in the dialog window."""
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        # Title ───────────────────────────────────────────────────────────────
        _label(outer, "Title *")
        self._title_var = tk.StringVar()
        _entry(outer, self._title_var)

        # Status ──────────────────────────────────────────────────────────────
        _label(outer, "Status *")
        statuses = self._controller.board.statuses
        if statuses:
            item_status_id = self._item.status_id if self._item else ""
            default_status = None
            for s in statuses:
                if s.id == item_status_id:
                    default_status = s
                    break
            if default_status is None:
                default_status = statuses[0]

            self._status_label_var = tk.StringVar(value=default_status.label)
            self._status_label_to_id = {s.label: s.id for s in statuses}
            combo = ttk.Combobox(
                outer, textvariable=self._status_label_var,
                values=[s.label for s in statuses],
                style="Dark.TCombobox", state="readonly", font=F_NORM,
            )
            combo.pack(fill="x", pady=(4, 12), ipady=4)
        else:
            tk.Label(outer, text="No statuses available — add one first.",
                     bg=BG, fg=RED, font=F_SM).pack(anchor="w", pady=(4, 12))
            self._status_label_var = None

        # Parent selector ─────────────────────────────────────────────────────
        self._parent_id_var = None
        if self._item_type != "epic":
            self._build_parent_selector(outer)

        # Due date ────────────────────────────────────────────────────────────
        _label(outer, "Due Date  (YYYY-MM-DD)")
        self._due_var = tk.StringVar()
        _entry(outer, self._due_var)

        # Description ─────────────────────────────────────────────────────────
        _label(outer, "Description")
        self._desc_text = tk.Text(outer, bg=BG_FIELD, fg=FG, font=F_NORM,
                                  relief="flat", height=5, insertbackground=FG, wrap="word")
        self._desc_text.pack(fill="x", pady=(4, 12))

        # Children section (edit mode — epic / task only) ─────────────────────
        if not self._is_create and self._item_type in ("epic", "task"):
            self._build_children_section(outer)

        # Error label ─────────────────────────────────────────────────────────
        self._error_var = tk.StringVar()
        tk.Label(outer, textvariable=self._error_var, bg=BG, fg=RED,
                 font=F_SM).pack(anchor="w", pady=(4, 0))

        # Buttons row ─────────────────────────────────────────────────────────
        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(anchor="e", pady=(8, 0))
        _btn(btn_row, "Cancel", self.destroy, bg="#334155").pack(side="left", padx=(0, 8))
        _btn(btn_row, "Save & Close", self._on_close).pack(side="left")

    def _build_parent_selector(self, parent):
        """Build a dropdown to select the parent Epic or Task."""
        board = self._controller.board
        if self._item_type == "task":
            _label(parent, "Parent Epic *")
            options = []
            for e in board.epics:
                options.append((e.id, e.title))
        else:
            _label(parent, "Parent Task *")
            options = []
            for e in board.epics:
                for t in e.children:
                    options.append((t.id, t.title))

        if not options:
            kind = "Epics" if self._item_type == "task" else "Tasks"
            tk.Label(parent, text=f"No {kind} available — create one first.",
                     bg=BG, fg=RED, font=F_SM).pack(anchor="w", pady=(4, 12))
            return

        label_to_id = {}
        for id_, title in options:
            label_to_id[title] = id_

        current_parent = board.find_parent(self._item.id) if self._item else None
        current_parent_id = current_parent.id if current_parent else self._parent_id

        default_title = options[0][1]
        for id_, title in options:
            if id_ == current_parent_id:
                default_title = title
                break

        display_var = tk.StringVar(value=default_title)
        self._parent_id_var = tk.StringVar(value=label_to_id[default_title])

        def on_change(*_):
            self._parent_id_var.set(label_to_id[display_var.get()])

        display_var.trace_add("write", on_change)

        titles = []
        for _, title in options:
            titles.append(title)
        combo = ttk.Combobox(
            parent, textvariable=display_var,
            values=titles,
            style="Dark.TCombobox", state="readonly", font=F_NORM,
        )
        combo.pack(fill="x", pady=(4, 12), ipady=4)

    def _build_children_section(self, parent):
        """Build the children list and add-child controls shown in edit mode."""
        tk.Frame(parent, bg="#334155", height=1).pack(fill="x", pady=(4, 12))
        _label(parent, CHILD_LABEL[self._item_type], font=F_BOLD, fg=FG)

        self._children_frame = tk.Frame(parent, bg=BG)
        self._children_frame.pack(fill="x", pady=(6, 0))
        self._refresh_children()

        add_row = tk.Frame(parent, bg=BG)
        add_row.pack(fill="x", pady=(8, 0))

        self._new_child_var = tk.StringVar()
        tk.Entry(add_row, textvariable=self._new_child_var, bg=BG_FIELD, fg=FG,
                 font=F_NORM, relief="flat", insertbackground=FG).pack(
                     side="left", fill="x", expand=True, ipady=4)

        _btn(add_row, "+ Add", self._on_add_child).pack(side="left", padx=(6, 0))

    def _refresh_children(self):
        """Rebuild the children list inside the edit dialog."""
        for w in self._children_frame.winfo_children():
            w.destroy()

        children = self._item.children if self._item else []
        if not children:
            tk.Label(self._children_frame, text="None yet.", bg=BG,
                     fg=FG_DIM, font=F_SM).pack(anchor="w")
            return

        for child in list(children):
            row = tk.Frame(self._children_frame, bg=BG_ROW)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=child.title, bg=BG_ROW, fg=FG, font=F_NORM,
                     anchor="w").pack(side="left", padx=8, pady=4, fill="x", expand=True)
            del_btn = tk.Label(row, text="✕", bg=BG_ROW, fg=RED,
                               font=F_BOLD, cursor="hand2", padx=8)
            del_btn.pack(side="right")
            del_btn.bind("<Button-1>", lambda e, cid=child.id: self._on_remove_child(cid))

    # ── children actions ──────────────────────────────────────────────────────

    def _on_add_child(self):
        """Read the new child title field and delegate creation to the controller."""
        title = self._new_child_var.get().strip()
        if not title:
            return
        try:
            self._controller.add_child_item(self._item.id, title)
            self._new_child_var.set("")
            self._refresh_children()
        except ValueError as ex:
            self._error_var.set(str(ex))

    def _on_remove_child(self, child_id):
        """Remove a child item and refresh the children list."""
        self._controller.remove_child_item(child_id)
        self._refresh_children()

    # ── populate (edit mode) ──────────────────────────────────────────────────

    def _populate(self):
        """Pre-fill all fields with the existing item's data."""
        self._title_var.set(self._item.title)
        if self._status_label_var:
            status = self._controller.board.get_status(self._item.status_id)
            if status:
                self._status_label_var.set(status.label)
        if self._item.due_date:
            self._due_var.set(self._item.due_date.isoformat())
        self._desc_text.insert("1.0", self._item.description)

    # ── save & close ──────────────────────────────────────────────────────────

    def _on_close(self):
        """Validate the form and delegate the create or update to the controller."""
        title = self._title_var.get().strip()
        if not title:
            self._error_var.set("Title is required.")
            return

        due = None
        due_str = self._due_var.get().strip()
        if due_str:
            try:
                due = date.fromisoformat(due_str)
            except ValueError:
                self._error_var.set("Invalid date — use YYYY-MM-DD.")
                return

        status_id = ""
        if self._status_label_var and self._status_label_var.get():
            status_id = self._status_label_to_id.get(self._status_label_var.get(), "")

        description = self._desc_text.get("1.0", "end-1c").strip()

        try:
            if self._is_create:
                self._create(title, description, status_id, due)
            else:
                self._update(title, description, status_id, due)
        except ValueError as ex:
            self._error_var.set(str(ex))
            return

        self.destroy()

    def _create(self, title, description, status_id, due):
        """Delegate item creation to the correct controller method based on item_type."""
        if self._item_type == "epic":
            self._controller.create_epic(title, description, status_id, due)

        elif self._item_type == "task":
            pid = self._parent_id_var.get() if self._parent_id_var else None
            if not pid:
                raise ValueError("Please select a parent Epic.")
            self._controller.create_task(title, pid, description, status_id, due)

        elif self._item_type == "child_task":
            pid = self._parent_id_var.get() if self._parent_id_var else None
            if not pid:
                raise ValueError("Please select a parent Task.")
            self._controller.create_child_task(title, pid, description, status_id, due)

    def _update(self, title, description, status_id, due):
        """Delegate item update to the controller."""
        parent_id = self._parent_id_var.get() if self._parent_id_var else None
        self._controller.update_item(
            self._item.id,
            title=title,
            description=description,
            status_id=status_id,
            due_date=due,
            parent_id=parent_id,
        )
