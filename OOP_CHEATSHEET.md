# OOP Concepts Cheatsheet — ISN Task Manager

This file explains every OOP concept used in this codebase, with concrete examples from the code.

---

## 1. Class

A **class** is a blueprint for creating objects. It groups related data (attributes) and behaviour (methods) together.

```python
class Status:
    def __init__(self, label: str, color: str = "#cccccc", order: int = 0):
        self.label = label
        self.color = color
        self.order = order
```

When you write `Status("Todo", "#64748B", 0)` you create an **instance** — a concrete object built from the blueprint.

---

## 2. `__init__` — The constructor

`__init__` is a special method Python calls automatically when you create an instance. It sets up the initial state of the object.

```python
class WorkItem(ABC):
    def __init__(self, title: str, description: str = "", ...):
        self.id = str(uuid.uuid4())   # each instance gets a unique id
        self.title = title
        self.description = description
```

The first parameter is always `self` — it refers to the instance being created.

---

## 3. Inheritance

**Inheritance** lets one class (the child) reuse and extend the code of another class (the parent). The child gets all the parent's attributes and methods for free.

```
WorkItem          ← abstract parent
  ├── Epic        ← child
  ├── Task        ← child
  └── ChildTask   ← child
```

In Python:

```python
class Epic(WorkItem):   # Epic inherits from WorkItem
    type = "epic"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # call the parent's __init__
        self.children: list[Task] = []
```

`super().__init__(...)` calls the parent class constructor. Without it, the attributes defined in `WorkItem.__init__` (like `self.id`, `self.title`) would never be set.

---

## 4. Abstract Base Class (ABC) and `@abstractmethod`

An **abstract class** cannot be instantiated directly — it is a contract that child classes must fulfil.

```python
from abc import ABC, abstractmethod

class WorkItem(ABC):

    @abstractmethod
    def to_dict(self) -> dict:
        pass
```

- `ABC` makes the class abstract.
- `@abstractmethod` marks a method that **every child class must implement**.
- If you try to create `WorkItem("title")` directly, Python raises a `TypeError`.
- If a child class (e.g. `Epic`) does not implement `to_dict`, Python also raises a `TypeError` when you try to instantiate it.

This is used here to guarantee that every work item type knows how to serialise itself.

---

## 5. `@property`

`@property` turns a method into an attribute you can read like a normal field, but the getter function is called under the hood.

```python
class BoardController:

    @property
    def board(self) -> Board:
        return self._board
```

Without `@property`, callers would write `controller.board()` (with parentheses). With it, they write `controller.board` — looks like an attribute, but it is actually calling the method. This lets you control access (make it read-only, add validation, etc.) without changing the calling code.

In `WorkItem`, `type` is declared as an abstract property so that subclasses **must** provide it:

```python
class WorkItem(ABC):

    @property
    @abstractmethod
    def type(self) -> str:
        pass
```

Subclasses satisfy this by setting a class-level attribute:

```python
class Epic(WorkItem):
    type = "epic"   # this overrides the abstract property
```

---

## 6. `@classmethod`

A **class method** receives the class itself (not an instance) as its first argument, conventionally named `cls`. It can be called on the class directly, without creating an instance first.

Used here for `from_dict` — a factory method that creates an instance from a dictionary:

```python
class Status:

    @classmethod
    def from_dict(cls, data: dict) -> Status:
        return cls(
            label=data["label"],
            color=data.get("color", "#cccccc"),
            status_id=data["id"],
        )
```

Calling `Status.from_dict({"id": "s1", "label": "Todo", ...})` creates and returns a new `Status` object. Because it uses `cls(...)` instead of `Status(...)`, it also works correctly if a subclass inherits this method.

---

## 7. `@staticmethod`

A **static method** belongs to the class for organisational reasons, but does not receive `self` or `cls`. It is just a plain function that lives inside the class namespace.

```python
class WorkItem:

    @staticmethod
    def _parse_date(value):
        return date.fromisoformat(value) if value else None
```

`_parse_date` does not need any data from a specific instance or the class itself — it only converts a string. Putting it inside `WorkItem` (rather than at module level) keeps related helpers together.

---

## 8. Polymorphism

**Polymorphism** means that different classes can respond to the same method call in different ways. Because `Epic`, `Task`, and `ChildTask` all implement `to_dict()`, you can call it on any work item without knowing which type it is:

```python
for item in board.all_items():
    data = item.to_dict()   # each type serialises itself differently
```

The same works in `from_dict` on `WorkItem`:

```python
@staticmethod
def from_dict(data: dict) -> WorkItem:
    kind = data.get("type")
    if kind == "epic":
        return Epic.from_dict(data)     # dispatches to the right subclass
    if kind == "task":
        return Task.from_dict(data)
    if kind == "child_task":
        return ChildTask.from_dict(data)
```

This is called **dispatch** — routing a call to the correct implementation based on a type tag.

---

## 9. Encapsulation

**Encapsulation** means hiding internal state and only exposing what the outside world needs.

- Attributes that start with `_` (single underscore) are private by convention — they signal "do not touch this from outside the class".
- Example: `BoardController._board` is private; external code reads the board through the `board` property.
- Example: `WorkItemCardView._item_id` is private; only the card itself knows it.

Python does not enforce this — it is a convention the team agrees to follow.

---

## 10. Composition

**Composition** means building complex objects by combining simpler ones. An `Epic` *has* a list of `Task`s; a `Task` *has* a list of `ChildTask`s.

```python
class Epic(WorkItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children: list[Task] = []
```

This is different from inheritance ("is a"). `Epic` is a `WorkItem` (inheritance), but it *has* `Task` children (composition).

---

## 11. Observer Pattern

The **observer pattern** lets one object notify others when something changes, without knowing who those others are.

```python
# Controller registers subscribers
def subscribe(self, callback) -> None:
    self._subscribers.append(callback)

# Controller notifies all subscribers after every mutation
def _notify(self) -> None:
    for cb in self._subscribers:
        cb()
```

```python
# The view registers itself
controller.subscribe(self.refresh)
```

When `create_epic` (or any mutation) runs, it calls `_notify()`, which calls `refresh()` on every registered view. The controller does not need to import the view class — it just calls whatever callable was registered. This keeps the layers decoupled.

---

## 12. `isinstance` checks

`isinstance(obj, SomeClass)` returns `True` if `obj` is an instance of `SomeClass` or any subclass of it. Used throughout the codebase to take different actions depending on the type of a work item:

```python
def add_child_item(self, parent_id: str, title: str) -> None:
    parent = self._board.find_by_id(parent_id)
    if isinstance(parent, Epic):
        self._board.add_task(Task(...), parent_id)
    elif isinstance(parent, Task):
        self._board.add_child_task(ChildTask(...), parent_id)
```

This is the controller deciding what to do based on the runtime type of the parent.

---

## 13. `**kwargs` — Keyword argument forwarding

`**kwargs` collects any named arguments into a dictionary. Used in `Task` and `Epic` to forward all constructor arguments to the parent without listing them explicitly:

```python
class Task(WorkItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)   # forward everything to WorkItem.__init__
        self.children = []
```

Without `**kwargs`, `Task.__init__` would have to repeat all of `WorkItem.__init__`'s parameters (`title`, `description`, `status_id`, …), which would create duplication.

---

## Quick reference table

| Concept | Where used in this project |
|---|---|
| Class | Every file — `Board`, `Status`, `Epic`, etc. |
| `__init__` | Every class |
| Inheritance | `Epic`, `Task`, `ChildTask` all inherit `WorkItem` |
| ABC / `@abstractmethod` | `WorkItem.to_dict`, `WorkItem.type` |
| `@property` | `BoardController.board`, `WorkItem.type` |
| `@classmethod` | `from_dict` on every model class |
| `@staticmethod` | `WorkItem.from_dict`, `_parse_date`, `_parse_datetime` |
| Polymorphism | `to_dict()` called on any work item type |
| Encapsulation | `_board`, `_subscribers`, `_item_id`, etc. |
| Composition | `Epic` has `Task` children; `Task` has `ChildTask` children |
| Observer pattern | `BoardController.subscribe` / `_notify` |
| `isinstance` | `BoardController.add_child_item`, `reparent`, etc. |
| `**kwargs` | `Task.__init__`, `Epic.__init__` |
