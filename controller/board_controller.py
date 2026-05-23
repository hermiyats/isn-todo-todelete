from __future__ import annotations
from model.board import Board
from model.work_item import Epic, Task, ChildTask
from model.status import Status
from model.json_repository import JsonRepository


class BoardController:
    def __init__(self, repo: JsonRepository | None = None):
        """Initialise the controller, loading the board from the repository."""
        self._repo: JsonRepository = repo or JsonRepository()
        self._board: Board = self._repo.load()
        self._subscribers: list = []

    # ── observer ──────────────────────────────────────────────────────

    @property
    def board(self) -> Board:
        """Return the current board (read-only access)."""
        return self._board

    def subscribe(self, callback) -> None:
        """Register a callback to be called whenever the board changes."""
        self._subscribers.append(callback)

    def _notify(self) -> None:
        for cb in self._subscribers:
            cb()

    # ── work item mutations ───────────────────────────────────────────

    def create_epic(self, title: str, description: str = "",
                    status_id: str = "", due_date=None) -> None:
        """Create a new Epic and add it to the board."""
        self._board.add_epic(
            Epic(title=title, description=description,
                 status_id=status_id, due_date=due_date)
        )
        self._save_and_notify()

    def create_task(self, title: str, parent_id: str,
                    description: str = "", status_id: str = "",
                    due_date=None) -> None:
        """Create a new Task under the specified Epic."""
        self._board.add_task(
            Task(title=title, description=description,
                 status_id=status_id, due_date=due_date),
            parent_id,
        )
        self._save_and_notify()

    def create_child_task(self, title: str, parent_id: str,
                          description: str = "", status_id: str = "",
                          due_date=None) -> None:
        """Create a new ChildTask under the specified Task."""
        self._board.add_child_task(
            ChildTask(title=title, description=description,
                      status_id=status_id, due_date=due_date),
            parent_id,
        )
        self._save_and_notify()

    def update_item(self, item_id: str, title: str, description: str,
                    status_id: str, due_date=None,
                    parent_id: str | None = None) -> None:
        """Update the fields of an existing work item, optionally reparenting it."""
        item = self._board.find_by_id(item_id)
        if item is None:
            raise ValueError(f"Item '{item_id}' not found")
        item.title       = title
        item.description = description
        item.status_id   = status_id
        item.due_date    = due_date
        if parent_id is not None:
            current = self._board.find_parent(item_id)
            if not current or current.id != parent_id:
                self._board.reparent(item_id, parent_id)
        self._save_and_notify()

    def add_child_item(self, parent_id: str, title: str) -> None:
        """Add a Task to an Epic, or a ChildTask to a Task."""
        parent = self._board.find_by_id(parent_id)
        if isinstance(parent, Epic):
            self._board.add_task(
                Task(title=title, status_id=parent.status_id), parent_id
            )
        elif isinstance(parent, Task):
            self._board.add_child_task(
                ChildTask(title=title, status_id=parent.status_id), parent_id
            )
        else:
            raise ValueError(f"Cannot add child to item '{parent_id}'")
        self._save_and_notify()

    def remove_child_item(self, child_id: str) -> None:
        """Remove a Task from its Epic, or a ChildTask from its Task."""
        parent = self._board.find_parent(child_id)
        if isinstance(parent, Epic):
            self._board.remove_task(child_id)
        elif isinstance(parent, Task):
            self._board.remove_child_task(child_id)
        else:
            raise ValueError(f"Item '{child_id}' has no removable parent")
        self._save_and_notify()

    def delete_item(self, item_id: str) -> None:
        """Delete a work item, raising ValueError if it still has children."""
        item = self._board.find_by_id(item_id)
        if item is None:
            raise ValueError(f"Item '{item_id}' not found")
        if hasattr(item, "children") and item.children:
            raise ValueError("Cannot delete: remove all children first.")
        parent = self._board.find_parent(item_id)
        if parent is None:
            self._board.remove_epic(item_id)
        elif hasattr(parent, "children"):
            from model.work_item import Epic
            if isinstance(parent, Epic):
                self._board.remove_task(item_id)
            else:
                self._board.remove_child_task(item_id)
        self._save_and_notify()

    def move_item(self, item_id: str, status_id: str) -> None:
        """Move a work item to a different status column."""
        self._board.move_item(item_id, status_id)
        self._save_and_notify()

    # ── status mutations ──────────────────────────────────────────────

    def add_status(self, label: str, color: str) -> None:
        """Create and add a new status column to the board."""
        order = max((s.order for s in self._board.statuses), default=-1) + 1
        self._board.add_status(Status(label, color, order))
        self._save_and_notify()

    def delete_status(self, status_id: str) -> None:
        """Delete a status column, raising ValueError if items are still using it."""
        self._board.remove_status(status_id)
        self._save_and_notify()

    def move_status_left(self, status_id: str) -> None:
        """Shift a status column one position to the left."""
        self._board.move_status_left(status_id)
        self._save_and_notify()

    def move_status_right(self, status_id: str) -> None:
        """Shift a status column one position to the right."""
        self._board.move_status_right(status_id)
        self._save_and_notify()

    # ── private ───────────────────────────────────────────────────────

    def _save_and_notify(self) -> None:
        self._repo.save(self._board)
        self._notify()
