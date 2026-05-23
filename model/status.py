from __future__ import annotations
import uuid
from typing import Optional


class Status:
    def __init__(
        self,
        label: str,
        color: str = "#cccccc",
        order: int = 0,
        status_id: Optional[str] = None,
    ):
        """Initialise a Status with a label, display color, and sort order."""
        self.id: str = status_id or str(uuid.uuid4())
        self.label: str = label
        self.color: str = color
        self.order: int = order

    def to_dict(self) -> dict:
        """Serialise this status to a plain dictionary for JSON storage."""
        return {
            "id": self.id,
            "label": self.label,
            "color": self.color,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Status:
        """Deserialise a Status from a dictionary."""
        return cls(
            label=data["label"],
            color=data.get("color", "#cccccc"),
            order=data.get("order", 0),
            status_id=data["id"],
        )
