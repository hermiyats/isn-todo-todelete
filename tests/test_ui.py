"""
UI logic tests — no human interaction required.
A hidden Tk root is created once for the module; each test instantiates
widgets, drives them programmatically, then checks board/controller state.
"""
import pytest
import tkinter as tk
from datetime import date

from model.board import Board
from model.work_item import Epic, Task, ChildTask
from model.status import Status
from controller.board_controller import BoardController
from view.work_item_dialog import WorkItemDialog
from view.work_item_card_view import WorkItemCardView
from view.kanban_board_view import KanbanBoardView


# ── mock & fixtures ───────────────────────────────────────────────────────────

class _MockRepo:
    """Repository stub that never touches the filesystem."""

    def __init__(self, board):
        self._board = board

    def load(self):
        return self._board

    def save(self, board):
        pass


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def board():
    """Board with two statuses: todo (order 0) and in_progress (order 1)."""
    b = Board()
    b.add_status(Status("To Do",       "#cccccc", 0, status_id="todo"))
    b.add_status(Status("In Progress", "#4CAF50", 1, status_id="in_progress"))
    return b


@pytest.fixture
def populated_board(board):
    """Board pre-filled with one epic → one task → one child task, all in 'todo'."""
    epic  = Epic(title="Epic 1",  status_id="todo")
    board.add_epic(epic)
    task  = Task(title="Task 1",  status_id="todo")
    board.add_task(task, epic.id)
    child = ChildTask(title="Child 1", status_id="todo")
    board.add_child_task(child, task.id)
    return board, epic, task, child


def _make_controller(board):
    """Return a BoardController backed by the given board (no filesystem I/O)."""
    return BoardController(repo=_MockRepo(board))


def _dialog(tk_root, board, item_type, item=None, parent_id=None):
    """Open a WorkItemDialog in a test-friendly way."""
    controller = _make_controller(board)
    return WorkItemDialog(tk_root, controller, item_type,
                          item=item, parent_id=parent_id)


def _card_count(col):
    """Return the number of cards rendered inside a StatusColumnView."""
    canvas = None
    for w in col.winfo_children():
        if isinstance(w, tk.Canvas):
            canvas = w
            break
    if canvas is None:
        return 0
    container = canvas.winfo_children()[0]
    return len(container.winfo_children())


# ── KanbanBoardView ───────────────────────────────────────────────────────────

def test_kanban_column_count_matches_statuses(tk_root, board):
    kbv = KanbanBoardView(tk_root)
    kbv.refresh(board, on_card_click=lambda x: None, on_delete_status=lambda x: None)
    assert len(kbv._columns) == 2
    kbv.destroy()


def test_kanban_column_count_with_no_statuses(tk_root):
    empty_board = Board()
    kbv = KanbanBoardView(tk_root)
    kbv.refresh(empty_board, on_card_click=lambda x: None, on_delete_status=lambda x: None)
    assert len(kbv._columns) == 0
    kbv.destroy()


def test_kanban_items_go_to_correct_column(tk_root, board):
    epic_todo     = Epic(title="Todo Epic",     status_id="todo")
    epic_progress = Epic(title="Progress Epic", status_id="in_progress")
    board.add_epic(epic_todo)
    board.add_epic(epic_progress)

    kbv = KanbanBoardView(tk_root)
    kbv.refresh(board, on_card_click=lambda x: None, on_delete_status=lambda x: None)

    # columns are sorted by status.order: todo(0), in_progress(1)
    todo_col     = kbv._columns[0]
    progress_col = kbv._columns[1]

    assert _card_count(todo_col)     == 1
    assert _card_count(progress_col) == 1
    kbv.destroy()


def test_kanban_refresh_rebuilds_columns(tk_root, board):
    kbv = KanbanBoardView(tk_root)
    kbv.refresh(board, on_card_click=lambda x: None, on_delete_status=lambda x: None)
    assert len(kbv._columns) == 2

    # add a third status and refresh — columns must update
    board.add_status(Status("Done", "#22C55E", 2, status_id="done"))
    kbv.refresh(board, on_card_click=lambda x: None, on_delete_status=lambda x: None)
    assert len(kbv._columns) == 3
    kbv.destroy()


# ── WorkItemCardView ──────────────────────────────────────────────────────────

def test_card_click_fires_callback(tk_root, board):
    epic = Epic(title="Clickable Epic", status_id="todo")
    board.add_epic(epic)

    clicked_ids = []
    def on_click(item_id):
        clicked_ids.append(item_id)

    card = WorkItemCardView(tk_root, epic, on_click=on_click)
    card._on_click_event(None)   # simulate a click
    assert clicked_ids == [epic.id]
    card.destroy()


def test_card_shows_correct_title(tk_root, board):
    epic = Epic(title="My Special Epic", status_id="todo")
    board.add_epic(epic)

    card = WorkItemCardView(tk_root, epic, on_click=lambda x: None)

    title_label = None
    for w in card.winfo_children():
        if isinstance(w, tk.Label) and w.cget("text") == "My Special Epic":
            title_label = w
            break

    assert title_label is not None
    card.destroy()


# ── BoardController — status management ──────────────────────────────────────

def test_controller_add_status(board):
    controller = _make_controller(board)
    initial_count = len(board.statuses)
    controller.add_status("Review", "#FF9900")
    assert len(board.statuses) == initial_count + 1

    new_status = None
    for s in board.statuses:
        if s.label == "Review":
            new_status = s
            break
    assert new_status is not None
    assert new_status.color == "#FF9900"


def test_controller_delete_status(board):
    board.add_status(Status("Review", "#FF9900", 2, status_id="review"))
    controller = _make_controller(board)
    controller.delete_status("review")
    assert board.get_status("review") is None


def test_controller_delete_status_blocked_by_items(board):
    controller = _make_controller(board)
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    with pytest.raises(ValueError, match="Cannot delete status"):
        controller.delete_status("todo")


def test_controller_move_status_left(board):
    controller = _make_controller(board)
    controller.move_status_left("in_progress")
    todo        = board.get_status("todo")
    in_progress = board.get_status("in_progress")
    assert in_progress.order < todo.order


def test_controller_move_status_right(board):
    controller = _make_controller(board)
    controller.move_status_right("todo")
    todo        = board.get_status("todo")
    in_progress = board.get_status("in_progress")
    assert todo.order > in_progress.order


# ── WorkItemDialog — create mode ──────────────────────────────────────────────

def test_dialog_create_epic(tk_root, board):
    d = _dialog(tk_root, board, "epic")
    d._title_var.set("Brand New Epic")
    d._on_close()
    assert len(board.epics) == 1
    assert board.epics[0].title == "Brand New Epic"


def test_dialog_create_epic_with_due_date(tk_root, board):
    d = _dialog(tk_root, board, "epic")
    d._title_var.set("Dated Epic")
    d._due_var.set("2026-12-31")
    d._on_close()
    assert board.epics[0].due_date == date(2026, 12, 31)


def test_dialog_create_epic_with_description(tk_root, board):
    d = _dialog(tk_root, board, "epic")
    d._title_var.set("Described Epic")
    d._desc_text.insert("1.0", "Some description")
    d._on_close()
    assert board.epics[0].description == "Some description"


def test_dialog_create_task_under_epic(tk_root, board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    d = _dialog(tk_root, board, "task", parent_id=epic.id)
    d._title_var.set("New Task")
    d._on_close()
    assert len(epic.children) == 1
    assert epic.children[0].title == "New Task"


def test_dialog_create_child_task_under_task(tk_root, board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    d = _dialog(tk_root, board, "child_task", parent_id=task.id)
    d._title_var.set("New Sub-task")
    d._on_close()
    assert len(task.children) == 1
    assert task.children[0].title == "New Sub-task"


# ── WorkItemDialog — validation ───────────────────────────────────────────────

def test_dialog_empty_title_shows_error(tk_root, board):
    d = _dialog(tk_root, board, "epic")
    d._title_var.set("")
    d._on_close()
    assert d._error_var.get() == "Title is required."
    assert len(board.epics) == 0
    d.destroy()


def test_dialog_bad_date_shows_error(tk_root, board):
    d = _dialog(tk_root, board, "epic")
    d._title_var.set("Epic")
    d._due_var.set("not-a-date")
    d._on_close()
    assert "YYYY-MM-DD" in d._error_var.get()
    assert len(board.epics) == 0
    d.destroy()


def test_dialog_invalid_date_value_shows_error(tk_root, board):
    d = _dialog(tk_root, board, "epic")
    d._title_var.set("Epic")
    d._due_var.set("2026-13-99")   # month 13 does not exist
    d._on_close()
    assert d._error_var.get() != ""
    assert len(board.epics) == 0
    d.destroy()


# ── WorkItemDialog — edit mode ────────────────────────────────────────────────

def test_dialog_edit_prepopulates_fields(tk_root, populated_board):
    board, epic, task, child = populated_board
    d = _dialog(tk_root, board, "epic", item=epic)
    assert d._title_var.get() == "Epic 1"
    assert d._desc_text.get("1.0", "end-1c") == epic.description
    d.destroy()


def test_dialog_edit_updates_title(tk_root, populated_board):
    board, epic, task, child = populated_board
    d = _dialog(tk_root, board, "epic", item=epic)
    d._title_var.set("Updated Epic")
    d._on_close()
    assert epic.title == "Updated Epic"


def test_dialog_edit_updates_due_date(tk_root, populated_board):
    board, epic, task, child = populated_board
    d = _dialog(tk_root, board, "epic", item=epic)
    d._title_var.set(epic.title)
    d._due_var.set("2027-06-15")
    d._on_close()
    assert epic.due_date == date(2027, 6, 15)


def test_dialog_edit_clears_due_date(tk_root, populated_board):
    board, epic, task, child = populated_board
    epic.due_date = date(2027, 1, 1)
    d = _dialog(tk_root, board, "epic", item=epic)
    d._title_var.set(epic.title)
    d._due_var.set("")   # clear the due date
    d._on_close()
    assert epic.due_date is None


def test_dialog_edit_changes_status(tk_root, populated_board):
    board, epic, task, child = populated_board
    d = _dialog(tk_root, board, "epic", item=epic)
    d._title_var.set(epic.title)
    d._status_label_var.set("In Progress")
    d._on_close()
    assert epic.status_id == "in_progress"


# ── WorkItemDialog — children management ─────────────────────────────────────

def test_dialog_add_task_to_epic(tk_root, populated_board):
    board, epic, task, child = populated_board
    initial_count = len(epic.children)
    d = _dialog(tk_root, board, "epic", item=epic)
    d._new_child_var.set("New Task from Dialog")
    d._on_add_child()
    assert len(epic.children) == initial_count + 1
    assert epic.children[-1].title == "New Task from Dialog"
    d.destroy()


def test_dialog_remove_task_from_epic(tk_root, populated_board):
    board, epic, task, child = populated_board
    initial_count = len(epic.children)
    d = _dialog(tk_root, board, "epic", item=epic)
    d._on_remove_child(task.id)
    assert len(epic.children) == initial_count - 1
    d.destroy()


def test_dialog_add_child_task_to_task(tk_root, populated_board):
    board, epic, task, child = populated_board
    initial_count = len(task.children)
    d = _dialog(tk_root, board, "task", item=task)
    d._new_child_var.set("New Sub-task from Dialog")
    d._on_add_child()
    assert len(task.children) == initial_count + 1
    assert task.children[-1].title == "New Sub-task from Dialog"
    d.destroy()


def test_dialog_remove_child_task_from_task(tk_root, populated_board):
    board, epic, task, child = populated_board
    initial_count = len(task.children)
    d = _dialog(tk_root, board, "task", item=task)
    d._on_remove_child(child.id)
    assert len(task.children) == initial_count - 1
    d.destroy()


# ── WorkItemDialog — reparenting ──────────────────────────────────────────────

def test_dialog_reparent_task(tk_root, board):
    e1 = Epic(title="Epic 1", status_id="todo")
    e2 = Epic(title="Epic 2", status_id="todo")
    board.add_epic(e1)
    board.add_epic(e2)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, e1.id)

    d = _dialog(tk_root, board, "task", item=task)
    d._parent_id_var.set(e2.id)   # switch parent to e2
    d._title_var.set(task.title)
    d._on_close()

    assert task not in e1.children
    assert task in e2.children


def test_dialog_reparent_child_task(tk_root, board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    t1 = Task(title="Task 1", status_id="todo")
    t2 = Task(title="Task 2", status_id="todo")
    board.add_task(t1, epic.id)
    board.add_task(t2, epic.id)
    child = ChildTask(title="Child 1", status_id="todo")
    board.add_child_task(child, t1.id)

    d = _dialog(tk_root, board, "child_task", item=child)
    d._parent_id_var.set(t2.id)   # switch parent to t2
    d._title_var.set(child.title)
    d._on_close()

    assert child not in t1.children
    assert child in t2.children
