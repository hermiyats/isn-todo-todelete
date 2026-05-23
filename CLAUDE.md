# ISN Task Manager — CLAUDE.md

## What this project is
Kanban-style task manager for the ISN course at INSA Lyon.
School project following the conception doc (Étape 2) in Google Drive → folder "ISN" → file `Etape2_Conception`.
GitLab: `gitlab.insa-lyon.fr/sdegemen/todo-isn`

## Stack
- **Python** `/opt/homebrew/bin/python3` (3.14, Homebrew)
- **GUI** PyQt5 ≥ 5.15
- **Charts** matplotlib ≥ 3.7
- **Persistence** JSON file at `data/board.json` (auto-created at runtime)
- **Tests** pytest — run with `/opt/homebrew/bin/python3 -m pytest tests/ -v`

## Architecture — strict MVC
Three packages, zero cross-layer imports except through the controller:

| Layer | Package | Rule |
|---|---|---|
| Model | `model/` | Pure Python — **no Qt imports** |
| Controller | `controller/` | Bridges model ↔ view via observer pattern |
| View | `view/` | Qt widgets only — **no business logic** |

Observer pattern: views call `board_controller.subscribe(callback)`, controller calls `_notify()` after every mutation.

## Key classes

### Model
| Class | File | Purpose |
|---|---|---|
| `WorkItem` | `work_item.py` | Abstract base — `id, title, description, status_id, due_date, created_at` |
| `Epic` | `work_item.py` | Top-level item, contains `Task` list |
| `Task` | `work_item.py` | Mid-level, contains `ChildTask` list |
| `ChildTask` | `work_item.py` | Leaf node |
| `Board` | `board.py` | Aggregate root — holds epics + statuses, maintains O(1) `_index: dict[id → WorkItem]` |
| `Status` | `status.py` | `id, label, color, order` |
| `WiqlEngine` | `wiql_engine.py` | `parse(query) → AST`, `evaluate(items, query) → list[WorkItem]` |
| `JsonRepository` | `json_repository.py` | `load(path) → Board`, `save(board, path)` |

### Controller
| Class | File | Purpose |
|---|---|---|
| `BoardController` | `board_controller.py` | `create_epic/task/child_task`, `update_item`, `delete_item`, `on_move` |
| `FilterController` | `filter_controller.py` | `execute(query)`, `clear()` — emits results via callback |
| `PersistenceController` | `persistence_controller.py` | `load() → Board`, `save(board)` — default path `data/board.json` |

### View
| Class | File | Purpose |
|---|---|---|
| `MainWindow` | `main_window.py` | Root window — wires everything together |
| `KanbanBoardView` | `kanban_board_view.py` | `refresh(board, visible_items)` — rebuilds columns |
| `StatusColumnView` | `status_column_view.py` | Accepts Qt drag-drops, emits `card_dropped(item_id, status_id)` |
| `WorkItemCardView` | `work_item_card_view.py` | Draggable card, emits `clicked(item_id)` |
| `WorkItemDialog` | `work_item_dialog.py` | Modal form — `values() → dict` with `title, description, status_id, due_date` |
| `FilterBarView` | `filter_bar_view.py` | WIQL input, emits `query_submitted(str)` and `filter_cleared()` |
| `ChartWindow` | `chart_window.py` | matplotlib bar chart (items per status) |

## WIQL syntax
```
[NOT] <field> <op> '<value>'  [AND|OR ...]

Fields:   title, description, status, due_date, type
Ops:      =  !=  contains  startswith
Groups:   ( )
Logic:    AND  OR  NOT

Examples:
  title contains 'bug'
  status = 's1' AND NOT title contains 'wont'
  (type = 'epic' OR type = 'task') AND due_date startswith '2026'
```

## Iteration status

### ✅ Iteration 1 (done — 2026-05-17)
- Full MVC structure in place, app launches correctly
- WIQL engine with Lexer + recursive-descent Parser + AST Evaluator
- Drag-and-drop card movement between columns
- JSON auto-save on every board mutation
- 14 pytest tests — all green

### 🔲 Iteration 2 (todo)
- UI for creating Tasks and ChildTasks (only Epics wired up via `+ Epic`)
- Status column management (add / rename / delete columns)
- QSS stylesheet / visual theme
- `.gitignore`
- Visual drag-and-drop polish (ghost preview, insert indicator)
- ChartWindow: burndown + velocity views

## Running the app
```bash
cd /Users/hermes/repos/todo-isn/.claude/worktrees/competent-pascal-05d8a8
/opt/homebrew/bin/python3 main.py
```

## Running tests
```bash
/opt/homebrew/bin/python3 -m pytest tests/ -v
```

## Conventions
- All model classes implement `to_dict() / from_dict()` for JSON round-trips
- `Board._reindex()` must be called after any structural mutation (add/remove task or child)
- New view signals always use `str` item IDs — never pass `WorkItem` objects across the view/controller boundary
- Controller methods accept `**kwargs` that match `WorkItem` field names exactly (`title`, `description`, `status_id`, `due_date`)
