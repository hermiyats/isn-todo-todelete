"""Tests for the WIQL query engine (FROM … SELECT … WHERE …)."""
import pytest
from datetime import date

from model.board import Board
from model.status import Status
from model.work_item import Epic, Task, ChildTask
from model.wiql_engine import WiqlEngine, LexError, ParseError


# ── Sample-board fixture ──────────────────────────────────────────────────────
#
# Statuses  : todo | in_progress | done | blocked
#
# Epics
#   e1  title="ITOPS Infrastructure"   status=todo
#   e2  title="Ali"                    status=done
#   e3  title="Mobile App"             status=in_progress
#
# Tasks
#   t1  title="ITOPS Server Setup"     status=in_progress   (child of e1)
#   t2  title="Database Migration"     status=todo          (child of e1)
#   t3  title="Ali Review"             status=done          (child of e2)
#   t4  title="UI Design"              status=in_progress   (child of e3)
#
# ChildTasks
#   c1  title="ITOPS Nginx Config"     status=done          (child of t1)
#   c2  title="Write Ali Script"       status=todo          (child of t2)
#   c3  title="Create Wireframes"      status=in_progress   (child of t4)


@pytest.fixture
def engine():
    return WiqlEngine()


@pytest.fixture
def board():
    b = Board()
    b.add_status(Status("Todo",        "#cccccc", 0, status_id="todo"))
    b.add_status(Status("In Progress", "#4CAF50", 1, status_id="in_progress"))
    b.add_status(Status("Done",        "#2196F3", 2, status_id="done"))
    b.add_status(Status("Blocked",     "#FF5722", 3, status_id="blocked"))

    e1 = Epic(title="ITOPS Infrastructure", description="IT operations work",          status_id="todo")
    e2 = Epic(title="Ali",                  description="Ali personal project",         status_id="done")
    e3 = Epic(title="Mobile App",           description="Mobile application project",   status_id="in_progress")
    for e in (e1, e2, e3):
        b.add_epic(e)

    t1 = Task(title="ITOPS Server Setup",  description="Setup servers",            status_id="in_progress")
    t2 = Task(title="Database Migration",  description="Migrate old database",     status_id="todo")
    t3 = Task(title="Ali Review",          description="Code review by Ali",       status_id="done")
    t4 = Task(title="UI Design",           description="Design user interface",    status_id="in_progress")
    b.add_task(t1, e1.id)
    b.add_task(t2, e1.id)
    b.add_task(t3, e2.id)
    b.add_task(t4, e3.id)

    c1 = ChildTask(title="ITOPS Nginx Config",  description="Configure nginx on servers", status_id="done")
    c2 = ChildTask(title="Write Ali Script",    description="Automation script for Ali",  status_id="todo")
    c3 = ChildTask(title="Create Wireframes",   description="Draw UI wireframes",         status_id="in_progress")
    b.add_child_task(c1, t1.id)
    b.add_child_task(c2, t2.id)
    b.add_child_task(c3, t4.id)

    return b, dict(e1=e1, e2=e2, e3=e3, t1=t1, t2=t2, t3=t3, t4=t4, c1=c1, c2=c2, c3=c3)


# ── FROM type filtering ───────────────────────────────────────────────────────

def test_from_epic_only(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM EPIC SELECT * WHERE TITLE ~= "a"')
    for item in result:
        assert item.type == "epic"


def test_from_epics_plural_alias(engine, board):
    b, items = board
    r1 = engine.evaluate(b, 'FROM EPIC   SELECT * WHERE TITLE ~= "a"')
    r2 = engine.evaluate(b, 'FROM EPICS  SELECT * WHERE TITLE ~= "a"')
    assert set(i.id for i in r1) == set(i.id for i in r2)


def test_from_task_only(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM TASK SELECT * WHERE TITLE ~= "a"')
    for item in result:
        assert item.type == "task"


def test_from_subtask_alias(engine, board):
    b, items = board
    r1 = engine.evaluate(b, 'FROM SUBTASK    SELECT * WHERE TITLE ~= "a"')
    r2 = engine.evaluate(b, 'FROM CHILD_TASK SELECT * WHERE TITLE ~= "a"')
    assert set(i.id for i in r1) == set(i.id for i in r2)


def test_from_star_includes_all_types(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE ~= "a"')
    types = {i.type for i in result}
    assert "epic" in types
    assert "task" in types
    assert "child_task" in types


def test_from_comma_separated_types(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM EPIC, TASK SELECT * WHERE TITLE ~= "a"')
    for item in result:
        assert item.type in ("epic", "task")


# ── SELECT status filtering ───────────────────────────────────────────────────

def test_select_done_status(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM * SELECT DONE WHERE TITLE ~= "a"')
    for item in result:
        assert item.status_id == "done"


def test_select_star_any_status(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE ~= "a"')
    status_ids = {i.status_id for i in result}
    assert len(status_ids) > 1, "wildcard SELECT should return items from multiple statuses"


def test_select_case_insensitive(engine, board):
    b, items = board
    r_upper = engine.evaluate(b, 'FROM * SELECT DONE    WHERE TITLE ~= "a"')
    r_lower = engine.evaluate(b, 'FROM * SELECT done    WHERE TITLE ~= "a"')
    r_mixed = engine.evaluate(b, 'FROM * SELECT Done    WHERE TITLE ~= "a"')
    ids = set(i.id for i in r_upper)
    assert ids == set(i.id for i in r_lower) == set(i.id for i in r_mixed)


def test_select_underscore_normalized_to_space(engine, board):
    b, items = board
    # Status label is "In Progress"; query uses IN_PROGRESS
    r_underscore = engine.evaluate(b, 'FROM * SELECT IN_PROGRESS WHERE TITLE ~= "a"')
    r_quoted     = engine.evaluate(b, 'FROM * SELECT "In Progress" WHERE TITLE ~= "a"')
    assert set(i.id for i in r_underscore) == set(i.id for i in r_quoted)


def test_select_comma_separated_statuses(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM * SELECT DONE, TODO WHERE TITLE ~= "a"')
    for item in result:
        assert item.status_id in ("done", "todo")


def test_select_unknown_status_returns_empty(engine, board):
    b, _ = board
    result = engine.evaluate(b, 'FROM * SELECT NONEXISTENT WHERE TITLE ~= "a"')
    assert result == []


# ── WHERE field/operator filtering ───────────────────────────────────────────

def test_where_title_exact_match(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM EPIC SELECT * WHERE TITLE = "Ali"')
    assert len(result) == 1
    assert result[0] is items["e2"]


def test_where_title_exact_case_insensitive(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM EPIC SELECT * WHERE TITLE = "ali"')
    assert len(result) == 1
    assert result[0] is items["e2"]


def test_where_title_contains(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE ~= "ITOPS"')
    ids = {i.id for i in result}
    assert items["e1"].id in ids
    assert items["t1"].id in ids
    assert items["c1"].id in ids


def test_where_title_contains_case_insensitive(engine, board):
    b, items = board
    result_upper = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE ~= "ITOPS"')
    result_lower = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE ~= "itops"')
    assert {i.id for i in result_upper} == {i.id for i in result_lower}


def test_where_description_contains(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM * SELECT * WHERE DESCRIPTION ~= "Ali"')
    ids = {i.id for i in result}
    assert items["e2"].id in ids   # "Ali personal project"
    assert items["t3"].id in ids   # "Code review by Ali"
    assert items["c2"].id in ids   # "Automation script for Ali"


def test_where_description_exact(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM * SELECT * WHERE DESCRIPTION = "IT operations work"')
    assert len(result) == 1
    assert result[0] is items["e1"]


def test_where_duedate_exact(engine, board):
    b, items = board
    items["e1"].due_date = date(2026, 6, 1)
    result = engine.evaluate(b, 'FROM * SELECT * WHERE DUEDATE = "2026-06-01"')
    assert len(result) == 1
    assert result[0] is items["e1"]


def test_where_duedate_contains_year(engine, board):
    b, items = board
    items["e1"].due_date = date(2026, 6, 1)
    items["t1"].due_date = date(2026, 8, 15)
    items["e2"].due_date = date(2025, 12, 31)
    result = engine.evaluate(b, 'FROM * SELECT * WHERE DUEDATE ~= "2026"')
    ids = {i.id for i in result}
    assert items["e1"].id in ids
    assert items["t1"].id in ids
    assert items["e2"].id not in ids


def test_where_duedate_missing_returns_no_match(engine, board):
    b, items = board
    # No due dates set in fixture — exact match should return nothing
    result = engine.evaluate(b, 'FROM * SELECT * WHERE DUEDATE = "2026-06-01"')
    assert result == []


# ── Combined type + status + field ───────────────────────────────────────────

def test_combined_epic_done_title_contains(engine, board):
    b, items = board
    # e2 is epic, done, title "Ali" — matches
    result = engine.evaluate(b, 'FROM EPIC SELECT DONE WHERE TITLE ~= "Ali"')
    assert len(result) == 1
    assert result[0] is items["e2"]


def test_combined_star_done_title_contains_itops(engine, board):
    b, items = board
    # Only c1 is done AND has "ITOPS" in title
    result = engine.evaluate(b, 'FROM * SELECT DONE WHERE TITLE ~= "ITOPS"')
    assert len(result) == 1
    assert result[0] is items["c1"]


def test_combined_epic_star_title_exact_no_match(engine, board):
    b, items = board
    # No epic has exact title "ali project"
    result = engine.evaluate(b, 'FROM EPIC SELECT * WHERE TITLE = "ali project"')
    assert result == []


def test_combined_task_subtask_in_progress_title_contains(engine, board):
    b, items = board
    result = engine.evaluate(b, 'FROM TASK, SUBTASK SELECT IN_PROGRESS WHERE TITLE ~= "UI"')
    ids = {i.id for i in result}
    assert items["t4"].id in ids   # "UI Design", in_progress, task
    assert items["c3"].id not in ids  # "Create Wireframes" — no "UI" in title


def test_combined_subtask_done_description_contains(engine, board):
    b, items = board
    # c1 is done child_task, description "Configure nginx on servers"
    result = engine.evaluate(b, 'FROM SUBTASK SELECT DONE WHERE DESCRIPTION ~= "nginx"')
    assert len(result) == 1
    assert result[0] is items["c1"]


# ── Result ordering preserved ─────────────────────────────────────────────────

def test_result_order_matches_board_all_items(engine, board):
    b, _ = board
    all_items = b.all_items()
    result    = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE ~= "a"')
    all_ids   = [i.id for i in all_items if 'a' in i.title.lower()]
    result_ids = [i.id for i in result]
    assert result_ids == all_ids


# ── Lexer / parser errors ─────────────────────────────────────────────────────

def test_lex_error_unexpected_char(engine, board):
    b, _ = board
    with pytest.raises(LexError):
        engine.evaluate(b, 'FROM @ SELECT * WHERE TITLE = "x"')


def test_lex_error_unterminated_string(engine, board):
    b, _ = board
    with pytest.raises(LexError):
        engine.evaluate(b, "FROM * SELECT * WHERE TITLE = \"unclosed")


def test_parse_error_missing_from(engine, board):
    b, _ = board
    with pytest.raises(ParseError):
        engine.evaluate(b, 'SELECT * WHERE TITLE = "x"')


def test_parse_error_unknown_type(engine, board):
    b, _ = board
    with pytest.raises(ParseError):
        engine.evaluate(b, 'FROM STORY SELECT * WHERE TITLE = "x"')


def test_parse_error_unknown_field(engine, board):
    b, _ = board
    with pytest.raises(ParseError):
        engine.evaluate(b, 'FROM * SELECT * WHERE ASSIGNEE = "x"')


def test_parse_error_bad_operator(engine, board):
    # '!' is not a recognised operator — the lexer rejects it before the parser runs
    b, _ = board
    with pytest.raises((LexError, ParseError)):
        engine.evaluate(b, 'FROM * SELECT * WHERE TITLE != "x"')


def test_parse_error_value_must_be_quoted(engine, board):
    b, _ = board
    with pytest.raises(ParseError):
        engine.evaluate(b, 'FROM * SELECT * WHERE TITLE = unquoted')


def test_parse_error_trailing_garbage(engine, board):
    b, _ = board
    with pytest.raises(ParseError):
        engine.evaluate(b, 'FROM * SELECT * WHERE TITLE = "x" EXTRA')


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_board_returns_empty(engine):
    b = Board()
    b.add_status(Status("Done", "#2196F3", 0, status_id="done"))
    result = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE ~= "x"')
    assert result == []


def test_no_match_returns_empty_list(engine, board):
    b, _ = board
    result = engine.evaluate(b, 'FROM * SELECT * WHERE TITLE = "zzz_no_match"')
    assert result == []


def test_single_quotes_in_value(engine, board):
    b, items = board
    result = engine.evaluate(b, "FROM EPIC SELECT * WHERE TITLE = 'Ali'")
    assert len(result) == 1
    assert result[0] is items["e2"]


def test_field_keyword_case_insensitive(engine, board):
    b, items = board
    r1 = engine.evaluate(b, 'FROM EPIC SELECT * WHERE TITLE = "Ali"')
    r2 = engine.evaluate(b, 'FROM EPIC SELECT * WHERE title = "Ali"')
    assert [i.id for i in r1] == [i.id for i in r2]
