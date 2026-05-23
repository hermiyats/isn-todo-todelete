from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional


class WorkItem(ABC):
    def __init__(
        self,
        title: str,
        description: str = "",
        status_id: str = "",
        due_date: Optional[date] = None,
        item_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialise common fields shared by all work item types."""
        self.id: str = item_id or str(uuid.uuid4())
        self.title: str = title
        self.description: str = description
        self.status_id: str = status_id
        self.due_date: Optional[date] = due_date
        self.created_at: datetime = created_at or datetime.now()

    @property
    @abstractmethod
    def type(self) -> str:
        """Return the string type identifier for this work item."""
        pass

    def _base_dict(self) -> dict:
        """Return a dictionary with the fields common to all work item types."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "status_id": self.status_id,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
        }

    @abstractmethod
    def to_dict(self) -> dict:
        """Serialise this work item to a plain dictionary for JSON storage."""
        pass

    @staticmethod
    def from_dict(data: dict) -> WorkItem:
        """Dispatch to the correct subclass based on the 'type' field."""
        kind = data.get("type")
        if kind == "epic":
            return Epic.from_dict(data)
        if kind == "task":
            return Task.from_dict(data)
        if kind == "child_task":
            return ChildTask.from_dict(data)
        raise ValueError(f"Unknown work item type: '{kind}'")

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        """Parse an ISO-format date string, returning None if the value is absent."""
        return date.fromisoformat(value) if value else None

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse an ISO-format datetime string, returning None if the value is absent."""
        return datetime.fromisoformat(value) if value else None


class ChildTask(WorkItem):
    type = "child_task"

    def to_dict(self) -> dict:
        """Serialise this ChildTask to a dictionary."""
        return self._base_dict()

    @classmethod
    def from_dict(cls, data: dict) -> ChildTask:
        """Deserialise a ChildTask from a dictionary."""
        return cls(
            title=data["title"],
            description=data.get("description", ""),
            status_id=data.get("status_id", ""),
            due_date=cls._parse_date(data.get("due_date")),
            item_id=data["id"],
            created_at=cls._parse_datetime(data.get("created_at")),
        )


class Task(WorkItem):
    type = "task"

    def __init__(self, **kwargs):
        """Initialise a Task with an empty children list."""
        super().__init__(**kwargs)
        self.children: list[ChildTask] = []

    def to_dict(self) -> dict:
        """Serialise this Task and all its ChildTasks to a dictionary."""
        d = self._base_dict()
        child_dicts = []
        for child in self.children:
            child_dicts.append(child.to_dict())
        d["children"] = child_dicts
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Deserialise a Task and all its ChildTasks from a dictionary."""
        task = cls(
            title=data["title"],
            description=data.get("description", ""),
            status_id=data.get("status_id", ""),
            due_date=cls._parse_date(data.get("due_date")),
            item_id=data["id"],
            created_at=cls._parse_datetime(data.get("created_at")),
        )
        for child_data in data.get("children", []):
            task.children.append(ChildTask.from_dict(child_data))
        return task


class Epic(WorkItem):
    type = "epic"

    def __init__(self, **kwargs):
        """Initialise an Epic with an empty children list."""
        super().__init__(**kwargs)
        self.children: list[Task] = []

    def to_dict(self) -> dict:
        """Serialise this Epic and all its Tasks to a dictionary."""
        d = self._base_dict()
        task_dicts = []
        for task in self.children:
            task_dicts.append(task.to_dict())
        d["children"] = task_dicts
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Epic:
        """Deserialise an Epic and all its Tasks from a dictionary."""
        epic = cls(
            title=data["title"],
            description=data.get("description", ""),
            status_id=data.get("status_id", ""),
            due_date=cls._parse_date(data.get("due_date")),
            item_id=data["id"],
            created_at=cls._parse_datetime(data.get("created_at")),
        )
        for task_data in data.get("children", []):
            epic.children.append(Task.from_dict(task_data))
        return epic
