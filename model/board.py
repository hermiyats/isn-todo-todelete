from __future__ import annotations
from typing import Optional
from model.work_item import WorkItem, Epic, Task, ChildTask
from model.status import Status


class Board:
    def __init__(self):
        """Initialise an empty board with no epics or statuses."""
        self.epics: list[Epic] = []
        self.statuses: list[Status] = []

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def find_by_id(self, item_id: str) -> Optional[WorkItem]:
        """Search all epics, tasks, and child tasks and return the matching item."""
        for epic in self.epics:
            if epic.id == item_id:
                return epic
            for task in epic.children:
                if task.id == item_id:
                    return task
                for child in task.children:
                    if child.id == item_id:
                        return child
        return None

    def find_parent(self, item_id: str) -> Optional[WorkItem]:
        """Return the direct parent of the item with the given id."""
        for epic in self.epics:
            for task in epic.children:
                if task.id == item_id:
                    return epic
                for child in task.children:
                    if child.id == item_id:
                        return task
        return None

    def reparent(self, item_id: str, new_parent_id: str) -> None:
        """Move an item to a different parent, validating type compatibility."""
        item = self.find_by_id(item_id)
        if item is None:
            raise ValueError(f"Item '{item_id}' not found")

        old_parent = self.find_parent(item_id)
        new_parent = self.find_by_id(new_parent_id)

        if isinstance(item, Task):
            if not isinstance(new_parent, Epic):
                raise ValueError("A Task must be parented to an Epic")
            if old_parent:
                remaining = []
                for t in old_parent.children:
                    if t.id != item_id:
                        remaining.append(t)
                old_parent.children = remaining
            new_parent.children.append(item)

        elif isinstance(item, ChildTask):
            if not isinstance(new_parent, Task):
                raise ValueError("A Sub-task must be parented to a Task")
            if old_parent:
                remaining = []
                for c in old_parent.children:
                    if c.id != item_id:
                        remaining.append(c)
                old_parent.children = remaining
            new_parent.children.append(item)

        else:
            raise ValueError("Epics cannot be reparented")

    def all_items(self) -> list[WorkItem]:
        """Return a flat list of every work item on the board."""
        items = []
        for epic in self.epics:
            items.append(epic)
            for task in epic.children:
                items.append(task)
                items.extend(task.children)
        return items

    # ------------------------------------------------------------------
    # Statuses
    # ------------------------------------------------------------------

    def add_status(self, status: Status) -> None:
        """Add a status to the board, raising ValueError if the label already exists."""
        normalized = status.label.strip().lower()
        for existing in self.statuses:
            if existing.label.strip().lower() == normalized:
                raise ValueError(f"Status '{status.label}' already exists")
        self.statuses.append(status)

    def get_status(self, status_id: str) -> Optional[Status]:
        """Return the status with the given id, or None if not found."""
        for status in self.statuses:
            if status.id == status_id:
                return status
        return None

    def move_status_left(self, status_id: str) -> None:
        """Swap this status with the one immediately to its left."""
        ordered = sorted(self.statuses, key=lambda s: s.order)
        idx = None
        for i, s in enumerate(ordered):
            if s.id == status_id:
                idx = i
                break
        if idx is None or idx == 0:
            return
        ordered[idx].order, ordered[idx - 1].order = ordered[idx - 1].order, ordered[idx].order

    def move_status_right(self, status_id: str) -> None:
        """Swap this status with the one immediately to its right."""
        ordered = sorted(self.statuses, key=lambda s: s.order)
        idx = None
        for i, s in enumerate(ordered):
            if s.id == status_id:
                idx = i
                break
        if idx is None or idx == len(ordered) - 1:
            return
        ordered[idx].order, ordered[idx + 1].order = ordered[idx + 1].order, ordered[idx].order

    def remove_status(self, status_id: str) -> None:
        """Remove a status, raising ValueError if any items are still assigned to it."""
        in_use = []
        for item in self.all_items():
            if item.status_id == status_id:
                in_use.append(item)
        if in_use:
            raise ValueError(
                f"Cannot delete status: {len(in_use)} item(s) still assigned to it"
            )
        remaining = []
        for s in self.statuses:
            if s.id != status_id:
                remaining.append(s)
        self.statuses = remaining

    def _validate_status(self, status_id: str) -> None:
        """Raise ValueError if the given status_id does not exist on this board."""
        if not self.get_status(status_id):
            raise ValueError(f"Status '{status_id}' does not exist on this board")

    # ------------------------------------------------------------------
    # Epics
    # ------------------------------------------------------------------

    def add_epic(self, epic: Epic) -> None:
        """Add an epic to the board after validating its status."""
        self._validate_status(epic.status_id)
        self.epics.append(epic)

    def remove_epic(self, epic_id: str) -> None:
        """Remove the epic with the given id and all its descendant tasks."""
        remaining = []
        for e in self.epics:
            if e.id != epic_id:
                remaining.append(e)
        self.epics = remaining

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def add_task(self, task: Task, epic_id: str) -> None:
        """Add a task to the specified epic after validating its status."""
        self._validate_status(task.status_id)
        epic = self.find_by_id(epic_id)
        if not isinstance(epic, Epic):
            raise ValueError(f"Epic '{epic_id}' not found")
        epic.children.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from whichever epic owns it."""
        for epic in self.epics:
            remaining = []
            for t in epic.children:
                if t.id != task_id:
                    remaining.append(t)
            epic.children = remaining

    # ------------------------------------------------------------------
    # ChildTasks
    # ------------------------------------------------------------------

    def add_child_task(self, child: ChildTask, task_id: str) -> None:
        """Add a child task to the specified task after validating its status."""
        self._validate_status(child.status_id)
        task = self.find_by_id(task_id)
        if not isinstance(task, Task):
            raise ValueError(f"Task '{task_id}' not found")
        task.children.append(child)

    def remove_child_task(self, child_id: str) -> None:
        """Remove the child task with the given id from whichever task owns it."""
        for epic in self.epics:
            for task in epic.children:
                remaining = []
                for c in task.children:
                    if c.id != child_id:
                        remaining.append(c)
                task.children = remaining

    # ------------------------------------------------------------------
    # Move
    # ------------------------------------------------------------------

    def move_item(self, item_id: str, status_id: str) -> None:
        """Change the status of the item with the given id."""
        self._validate_status(status_id)
        item = self.find_by_id(item_id)
        if item is None:
            raise ValueError(f"Item '{item_id}' not found")
        item.status_id = status_id
