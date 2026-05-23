import pytest
from model.board import Board
from model.work_item import Epic, Task, ChildTask
from model.status import Status


# ── fixtures ──────────────────────────────────────────────────────────────────

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


# ── Statuses ──────────────────────────────────────────────────────────────────

def test_add_status():
    b = Board()
    s = Status("Done", "#2196F3", 0, status_id="done")
    b.add_status(s)
    assert b.get_status("done") is s


def test_add_duplicate_status():
    b = Board()
    b.add_status(Status("To Do", "#cccccc", 0, status_id="todo"))
    with pytest.raises(ValueError, match="already exists"):
        b.add_status(Status("To Do", "#cccccc", 1, status_id="todo2"))


def test_add_duplicate_status_case_insensitive():
    b = Board()
    b.add_status(Status("To Do", "#cccccc", 0, status_id="todo"))
    with pytest.raises(ValueError, match="already exists"):
        b.add_status(Status("to do", "#cccccc", 1, status_id="todo2"))


def test_add_duplicate_status_whitespace():
    b = Board()
    b.add_status(Status("To Do", "#cccccc", 0, status_id="todo"))
    with pytest.raises(ValueError, match="already exists"):
        b.add_status(Status("  To Do  ", "#cccccc", 1, status_id="todo2"))


def test_remove_status_no_items(board):
    board.add_status(Status("Review", "#aaaaaa", 2, status_id="review"))
    board.remove_status("review")
    assert board.get_status("review") is None


def test_remove_status_blocked_by_assigned_items(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    with pytest.raises(ValueError, match="Cannot delete status"):
        board.remove_status("todo")


def test_remove_status_removes_only_the_target(board):
    board.remove_status("in_progress")
    assert board.get_status("todo") is not None
    assert board.get_status("in_progress") is None


def test_move_status_right_swaps_order(board):
    # todo is at order 0, in_progress at order 1 — move todo right
    board.move_status_right("todo")
    todo        = board.get_status("todo")
    in_progress = board.get_status("in_progress")
    assert todo.order > in_progress.order


def test_move_status_left_swaps_order(board):
    # in_progress is at order 1, todo at order 0 — move in_progress left
    board.move_status_left("in_progress")
    todo        = board.get_status("todo")
    in_progress = board.get_status("in_progress")
    assert in_progress.order < todo.order


def test_move_status_left_at_boundary_is_noop(board):
    original_order = board.get_status("todo").order
    board.move_status_left("todo")
    assert board.get_status("todo").order == original_order


def test_move_status_right_at_boundary_is_noop(board):
    original_order = board.get_status("in_progress").order
    board.move_status_right("in_progress")
    assert board.get_status("in_progress").order == original_order


# ── Epics ─────────────────────────────────────────────────────────────────────

def test_add_epic(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    assert board.find_by_id(epic.id) is epic


def test_add_epic_invalid_status(board):
    with pytest.raises(ValueError, match="Status 'nonexistent' does not exist"):
        board.add_epic(Epic(title="Bad Epic", status_id="nonexistent"))


def test_remove_epic(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    board.remove_epic(epic.id)
    assert board.find_by_id(epic.id) is None
    assert board.epics == []


# ── Tasks ─────────────────────────────────────────────────────────────────────

def test_add_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    assert board.find_by_id(task.id) is task


def test_add_task_invalid_status(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    with pytest.raises(ValueError, match="Status 'nonexistent' does not exist"):
        board.add_task(Task(title="Bad Task", status_id="nonexistent"), epic.id)


def test_add_task_invalid_epic(board):
    with pytest.raises(ValueError, match="Epic 'bad-id' not found"):
        board.add_task(Task(title="Task 1", status_id="todo"), "bad-id")


def test_remove_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    board.remove_task(task.id)
    assert board.find_by_id(task.id) is None
    assert epic.children == []


# ── ChildTasks ────────────────────────────────────────────────────────────────

def test_add_child_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    child = ChildTask(title="Child 1", status_id="todo")
    board.add_child_task(child, task.id)
    assert board.find_by_id(child.id) is child


def test_add_child_task_invalid_status(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    with pytest.raises(ValueError, match="Status 'nonexistent' does not exist"):
        board.add_child_task(ChildTask(title="Bad Child", status_id="nonexistent"), task.id)


def test_add_child_task_invalid_task(board):
    with pytest.raises(ValueError, match="Task 'bad-id' not found"):
        board.add_child_task(ChildTask(title="Child 1", status_id="todo"), "bad-id")


def test_remove_child_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    child = ChildTask(title="Child 1", status_id="todo")
    board.add_child_task(child, task.id)
    board.remove_child_task(child.id)
    assert board.find_by_id(child.id) is None
    assert task.children == []


# ── all_items ─────────────────────────────────────────────────────────────────

def test_all_items_returns_flat_list(populated_board):
    board, epic, task, child = populated_board
    items = board.all_items()
    assert epic  in items
    assert task  in items
    assert child in items
    assert len(items) == 3


def test_all_items_empty_board():
    b = Board()
    b.add_status(Status("Todo", "#cccccc", 0, status_id="todo"))
    assert b.all_items() == []


def test_all_items_order_epic_before_task(populated_board):
    board, epic, task, child = populated_board
    items = board.all_items()
    assert items.index(epic) < items.index(task)
    assert items.index(task) < items.index(child)


# ── move_item ─────────────────────────────────────────────────────────────────

def test_move_item(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    board.move_item(epic.id, "in_progress")
    assert epic.status_id == "in_progress"


def test_move_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    board.move_item(task.id, "in_progress")
    assert task.status_id == "in_progress"


def test_move_item_invalid_status(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    with pytest.raises(ValueError, match="Status 'nonexistent' does not exist"):
        board.move_item(epic.id, "nonexistent")


def test_move_item_not_found(board):
    with pytest.raises(ValueError, match="Item 'bad-id' not found"):
        board.move_item("bad-id", "todo")


# ── find_parent ───────────────────────────────────────────────────────────────

def test_find_parent_of_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    assert board.find_parent(task.id) is epic


def test_find_parent_of_child_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, epic.id)
    child = ChildTask(title="Child 1", status_id="todo")
    board.add_child_task(child, task.id)
    assert board.find_parent(child.id) is task


def test_find_parent_of_epic_returns_none(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    assert board.find_parent(epic.id) is None


def test_find_parent_unknown_id_returns_none(board):
    assert board.find_parent("nonexistent") is None


# ── reparent ──────────────────────────────────────────────────────────────────

def test_reparent_task_to_new_epic(board):
    e1 = Epic(title="Epic 1", status_id="todo")
    e2 = Epic(title="Epic 2", status_id="todo")
    board.add_epic(e1)
    board.add_epic(e2)
    task = Task(title="Task 1", status_id="todo")
    board.add_task(task, e1.id)

    board.reparent(task.id, e2.id)

    assert task not in e1.children
    assert task in e2.children
    assert board.find_parent(task.id) is e2


def test_reparent_child_task_to_new_task(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    t1 = Task(title="Task 1", status_id="todo")
    t2 = Task(title="Task 2", status_id="todo")
    board.add_task(t1, epic.id)
    board.add_task(t2, epic.id)
    child = ChildTask(title="Child 1", status_id="todo")
    board.add_child_task(child, t1.id)

    board.reparent(child.id, t2.id)

    assert child not in t1.children
    assert child in t2.children
    assert board.find_parent(child.id) is t2


def test_reparent_epic_raises(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    with pytest.raises(ValueError, match="cannot be reparented"):
        board.reparent(epic.id, "anything")


def test_reparent_task_to_task_raises(board):
    epic = Epic(title="Epic 1", status_id="todo")
    board.add_epic(epic)
    t1 = Task(title="Task 1", status_id="todo")
    t2 = Task(title="Task 2", status_id="todo")
    board.add_task(t1, epic.id)
    board.add_task(t2, epic.id)
    with pytest.raises(ValueError, match="must be parented to an Epic"):
        board.reparent(t1.id, t2.id)


def test_reparent_unknown_item_raises(board):
    with pytest.raises(ValueError, match="not found"):
        board.reparent("bad-id", "anything")


# ── JSON serialisation round-trip ─────────────────────────────────────────────

def test_epic_serialisation_round_trip(populated_board):
    board, epic, task, child = populated_board
    data = epic.to_dict()
    restored = Epic.from_dict(data)
    assert restored.id    == epic.id
    assert restored.title == epic.title
    assert len(restored.children) == 1
    assert restored.children[0].id == task.id


def test_task_serialisation_round_trip(populated_board):
    board, epic, task, child = populated_board
    data = task.to_dict()
    restored = Task.from_dict(data)
    assert restored.id    == task.id
    assert restored.title == task.title
    assert len(restored.children) == 1
    assert restored.children[0].id == child.id


def test_child_task_serialisation_round_trip(populated_board):
    board, epic, task, child = populated_board
    data = child.to_dict()
    restored = ChildTask.from_dict(data)
    assert restored.id    == child.id
    assert restored.title == child.title


def test_status_serialisation_round_trip():
    s = Status("Review", "#FF9900", 3, status_id="review")
    restored = Status.from_dict(s.to_dict())
    assert restored.id    == s.id
    assert restored.label == s.label
    assert restored.color == s.color
    assert restored.order == s.order
