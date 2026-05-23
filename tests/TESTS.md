# Test Suite — Board Model

Run with:
```bash
/opt/homebrew/bin/python3 -m pytest tests/ -v
```

All tests live in `test_board.py` and operate directly on the model layer (no UI, no files).
Each test starts from a fresh `Board` pre-loaded with two statuses: `"todo"` and `"in_progress"`.

---

## Statuses

### `test_add_status`
Creates an empty board, adds a status, and checks it can be retrieved by id.

---

## Epics

### `test_add_epic`
Adds an epic to the board and verifies it can be found by its id.

### `test_add_epic_invalid_status`
Tries to add an epic with a `status_id` that does not exist on the board.
Expected: raises `ValueError`.

### `test_remove_epic`
Adds an epic then removes it. Verifies it can no longer be found and the epics list is empty.

---

## Tasks

### `test_add_task`
Adds a task inside an existing epic and verifies it can be found by its id.

### `test_add_task_invalid_status`
Tries to add a task with a `status_id` that does not exist on the board.
Expected: raises `ValueError`.

### `test_add_task_invalid_epic`
Tries to add a task to an epic id that does not exist.
Expected: raises `ValueError`.

### `test_remove_task`
Adds a task to an epic then removes it. Verifies it can no longer be found and the epic's children list is empty.

---

## Child Tasks

### `test_add_child_task`
Adds a child task inside an existing task and verifies it can be found by its id.

### `test_add_child_task_invalid_status`
Tries to add a child task with a `status_id` that does not exist on the board.
Expected: raises `ValueError`.

### `test_add_child_task_invalid_task`
Tries to add a child task to a task id that does not exist.
Expected: raises `ValueError`.

### `test_remove_child_task`
Adds a child task to a task then removes it. Verifies it can no longer be found and the task's children list is empty.

---

## Moving Items Between Statuses

### `test_move_item`
Moves an epic from `"todo"` to `"in_progress"` and checks its `status_id` updated.

### `test_move_task`
Moves a task from `"todo"` to `"in_progress"` and checks its `status_id` updated.

### `test_move_item_invalid_status`
Tries to move an item to a `status_id` that does not exist on the board.
Expected: raises `ValueError`.

### `test_move_item_not_found`
Tries to move an item with an id that does not exist on the board.
Expected: raises `ValueError`.
