from __future__ import annotations
import json
import os
from model.board import Board
from model.work_item import Epic
from model.status import Status

WORK_ITEMS_FILE = "data/work_items.json"
STATUSES_FILE = "data/statuses.json"


class JsonRepository:
    def __init__(
        self,
        work_items_path: str = WORK_ITEMS_FILE,
        statuses_path: str = STATUSES_FILE,
    ):
        """Initialise with paths to the two JSON data files."""
        self.work_items_path = work_items_path
        self.statuses_path = statuses_path

    def save(self, board: Board) -> None:
        """Persist the board's epics and statuses to their respective JSON files."""
        os.makedirs(os.path.dirname(self.work_items_path), exist_ok=True)

        epics_data = []
        for epic in board.epics:
            epics_data.append(epic.to_dict())

        with open(self.work_items_path, "w") as f:
            json.dump(epics_data, f, indent=2)

        statuses_data = []
        for status in board.statuses:
            statuses_data.append(status.to_dict())

        with open(self.statuses_path, "w") as f:
            json.dump(statuses_data, f, indent=2)

    DEFAULT_STATUSES = [
        Status("Todo",        "#64748B", 0, status_id="todo"),
        Status("In Progress", "#3B82F6", 1, status_id="in_progress"),
        Status("Done",        "#22C55E", 2, status_id="done"),
    ]

    def load(self) -> Board:
        """Load a Board from disk, seeding default statuses if the file is missing."""
        board = Board()

        if os.path.exists(self.statuses_path):
            with open(self.statuses_path) as f:
                for status_data in json.load(f):
                    board.statuses.append(Status.from_dict(status_data))

        if not board.statuses:
            for s in self.DEFAULT_STATUSES:
                board.statuses.append(Status(s.label, s.color, s.order, status_id=s.id))

        if os.path.exists(self.work_items_path):
            with open(self.work_items_path) as f:
                for epic_data in json.load(f):
                    board.epics.append(Epic.from_dict(epic_data))

        return board
