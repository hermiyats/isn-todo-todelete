# ISN Task Manager — Architecture

## Overview

This app is a Kanban-style task manager built with Python and Tkinter. It follows a strict **MVC (Model-View-Controller)** architecture: the three layers never import each other directly, they communicate only through the controller.

```
┌─────────────────────────────────────┐
│              View (Tkinter UI)       │
│  MainWindow, KanbanBoardView, ...    │
└──────────────────┬──────────────────┘
                   │  calls methods on
                   ▼
┌─────────────────────────────────────┐
│           Controller layer           │
│         BoardController              │
│   subscribes views via callbacks     │
└───────────┬────────────┬────────────┘
            │ reads      │ writes
            ▼            ▼
┌─────────────────────────────────────┐
│             Model layer              │
│  Board, WorkItem, Status, ...        │
│  JsonRepository (persistence)        │
└─────────────────────────────────────┘
```

---

## Layer 1 — Model (`model/`)

The model contains pure Python classes with **no Tkinter imports**. It defines the data and the rules for changing it.

### `work_item.py` — The work item hierarchy

There are three levels of work items, forming a tree:

```
Epic
 └── Task
      └── ChildTask
```

All three inherit from `WorkItem`, which is an **abstract base class** (ABC). `WorkItem` defines the fields every item has:

| Field        | Type              | Description                     |
|--------------|-------------------|---------------------------------|
| `id`         | `str` (UUID)      | Unique identifier                |
| `title`      | `str`             | Display name                    |
| `description`| `str`             | Optional longer text            |
| `status_id`  | `str`             | Which column the card is in     |
| `due_date`   | `date` or `None`  | Optional deadline               |
| `created_at` | `datetime`        | When the item was created       |
| `type`       | `str` (abstract)  | `"epic"`, `"task"`, or `"child_task"` |

Each subclass also holds a `children` list:
- `Epic.children` → list of `Task`
- `Task.children` → list of `ChildTask`
- `ChildTask` has no children

Every class implements `to_dict()` / `from_dict()` for JSON serialisation.

### `board.py` — The aggregate root

`Board` owns the entire data tree. **All structural mutations go through `Board` methods** — nothing reaches into `epic.children` directly from outside this file.

Key methods:

| Method | What it does |
|---|---|
| `find_by_id(id)` | Walk the whole tree and return the matching item |
| `find_parent(id)` | Return the direct parent of an item |
| `add_epic / add_task / add_child_task` | Add items, validating status and parent type |
| `remove_epic / remove_task / remove_child_task` | Remove items by id |
| `move_item(id, status_id)` | Change which column a card belongs to |
| `reparent(id, new_parent_id)` | Move a Task to a different Epic, or a ChildTask to a different Task |
| `add_status / remove_status / move_status_left / move_status_right` | Manage columns |
| `all_items()` | Flat list of every item (used for filtering and display) |

### `status.py` — A Kanban column definition

`Status` is a simple data class with four fields: `id`, `label`, `color` (hex string), and `order` (integer for left-to-right position).

### `json_repository.py` — Persistence

`JsonRepository` saves and loads the board to two JSON files:
- `data/statuses.json` — list of status objects
- `data/work_items.json` — list of epics (with nested tasks and child tasks)

If no files exist yet, the repository seeds three default statuses: *Todo*, *In Progress*, *Done*.

### `wiql_engine.py` — Query engine *(not yet implemented)*

This file is a placeholder for a WIQL (Work Item Query Language) engine. The syntax will allow filtering cards by field, e.g.:

```
title contains 'bug' AND status = 'in_progress'
```

---

## Layer 2 — Controller (`controller/`)

### `board_controller.py` — The single controller

`BoardController` is the only entry point the view uses. It:
1. Loads the board from `JsonRepository` on startup.
2. Exposes **mutation methods** (`create_epic`, `move_item`, `add_status`, …).
3. After every mutation, calls `_save_and_notify()` which persists to disk and calls all subscriber callbacks.

**Observer pattern:**
```
view registers:  controller.subscribe(self.refresh)
mutation fires:  controller._notify()  →  calls refresh() on every subscriber
```

This means the view never polls — it is pushed an update whenever anything changes.

### `filter_controller.py` — WIQL filtering *(not yet implemented)*

Placeholder for a controller that will wrap `WiqlEngine` and expose `execute(query)` / `clear()`.

### `persistence_controller.py` — Thin wrapper

A thin wrapper around `JsonRepository`. Currently used directly by `BoardController`; may be split out if load/save become more complex.

---

## Layer 3 — View (`view/`)

All view classes are Tkinter widgets. They **never import from `model/`** — they receive plain Python objects from the controller and call controller methods in response to user events.

### `main_window.py` — Root window

`MainWindow` (extends `tk.Tk`) wires everything together:
- Builds the header bar (buttons), the board, and the footer.
- Subscribes `self.refresh` to the controller.
- `refresh()` calls `KanbanBoardView.refresh(board, callbacks)` on every board change.

### `kanban_board_view.py` — The board

`KanbanBoardView` (extends `tk.Frame`) renders one `StatusColumnView` per status column. On `refresh()` it destroys all existing columns and rebuilds them from scratch.

It also owns the **drag state**: when the user drags a card, this class creates a floating ghost window, highlights the target column, and fires `on_item_drop(item_id, status_id)` on release.

### `status_column_view.py` — One column

`StatusColumnView` renders:
- A colored top bar (the status color).
- A header row with the column name, left/right reorder arrows, item count badge, and delete button.
- A scrollable list of `WorkItemCardView` cards.

### `work_item_card_view.py` — One card

`WorkItemCardView` displays a single work item. It distinguishes a **click** (opens edit dialog) from a **drag** (moves card to another column) using a pixel threshold (`DRAG_THRESHOLD = 5`).

### `work_item_dialog.py` — Create / edit form

`WorkItemDialog` is a modal `tk.Toplevel` that covers both create and edit flows:
- **Create mode** (`item=None`): shows an empty form; Tasks and ChildTasks also show a parent selector dropdown.
- **Edit mode** (`item` set): pre-fills all fields; Epics and Tasks also show a children list with add/remove controls.

### `status_dialog.py` — Add a column

`StatusDialog` is a modal for creating new status columns. It provides color swatches and a hex input with a live preview.

### `filter_bar_view.py` — WIQL filter bar *(not yet implemented)*

### `chart_window.py` — Charts *(not yet implemented)*

---

## Data flow for a typical mutation

**User clicks "+ Epic" → fills the form → clicks "Save & Close":**

```
WorkItemDialog._on_close()
  → WorkItemDialog._create()
    → BoardController.create_epic(title, description, status_id, due)
      → Board.add_epic(Epic(...))          # model mutation
      → JsonRepository.save(board)         # persist to disk
      → BoardController._notify()          # fire all callbacks
        → MainWindow.refresh()
          → KanbanBoardView.refresh(board, ...)  # UI rebuilt
```

---

## What is missing (Iteration 2)

| Feature | Status | Notes |
|---|---|---|
| WIQL filter bar | Not started | `filter_bar_view.py`, `wiql_engine.py`, `filter_controller.py` are empty placeholders |
| Charts window | Not started | `chart_window.py` is an empty placeholder |
| QSS / visual theme | Not started | Currently using inline color constants |
| Drag-and-drop polish | Partial | Ghost preview works; no insert indicator between cards |
| Burndown / velocity charts | Not started | Needs date tracking on status changes |
| `.gitignore` | Missing | Should ignore `__pycache__/`, `*.pyc`, `data/` |
| Delete item from the board | Missing | The dialog has no delete button for the item itself |
| Delete Epic cascades tasks | Partial | `remove_epic` removes the epic but child tasks are orphaned on the data level if not careful |
