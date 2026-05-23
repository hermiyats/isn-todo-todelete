"""WIQL query engine: FROM <types> SELECT <statuses> WHERE <field> <op> <value>"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ── Token types ───────────────────────────────────────────────────────────────

class TT(Enum):
    FROM     = auto()
    SELECT   = auto()
    WHERE    = auto()
    STAR     = auto()
    COMMA    = auto()
    EQ       = auto()   # =
    CONTAINS = auto()   # ~=
    IDENT    = auto()
    STRING   = auto()
    EOF      = auto()


@dataclass
class Token:
    type:  TT
    value: str


# ── Lexer ─────────────────────────────────────────────────────────────────────

_KEYWORDS: dict[str, TT] = {
    "FROM":   TT.FROM,
    "SELECT": TT.SELECT,
    "WHERE":  TT.WHERE,
}


class LexError(ValueError):
    pass


class Lexer:
    def __init__(self, text: str):
        self._text = text
        self._pos  = 0

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self._pos < len(self._text):
            ch = self._text[self._pos]

            if ch.isspace():
                self._pos += 1
                continue

            if ch == '*':
                self._pos += 1
                tokens.append(Token(TT.STAR, '*'))

            elif ch == ',':
                self._pos += 1
                tokens.append(Token(TT.COMMA, ','))

            elif ch == '~':
                self._pos += 1
                if self._pos < len(self._text) and self._text[self._pos] == '=':
                    self._pos += 1
                    tokens.append(Token(TT.CONTAINS, '~='))
                else:
                    raise LexError(f"Expected '=' after '~' at position {self._pos}")

            elif ch == '=':
                self._pos += 1
                tokens.append(Token(TT.EQ, '='))

            elif ch in ('"', "'"):
                quote = ch
                self._pos += 1
                start = self._pos
                while self._pos < len(self._text) and self._text[self._pos] != quote:
                    self._pos += 1
                if self._pos >= len(self._text):
                    raise LexError("Unterminated string literal")
                value = self._text[start:self._pos]
                self._pos += 1  # closing quote
                tokens.append(Token(TT.STRING, value))

            elif ch.isalpha() or ch == '_':
                start = self._pos
                while self._pos < len(self._text) and (
                    self._text[self._pos].isalnum() or self._text[self._pos] == '_'
                ):
                    self._pos += 1
                raw = self._text[start:self._pos]
                tt  = _KEYWORDS.get(raw.upper(), TT.IDENT)
                tokens.append(Token(tt, raw))

            else:
                raise LexError(f"Unexpected character '{ch}' at position {self._pos}")

        tokens.append(Token(TT.EOF, ''))
        return tokens


# ── AST ───────────────────────────────────────────────────────────────────────

@dataclass
class Query:
    """Parsed WIQL query ready for evaluation."""
    types:    list[str]   # ['*'] or subset of {'epic', 'task', 'child_task'}
    statuses: list[str]   # ['*'] or list of normalised status labels
    field:    str         # 'title' | 'description' | 'duedate'
    op:       str         # '=' | '~='
    value:    str         # right-hand side comparison value


# ── Parser ────────────────────────────────────────────────────────────────────

# Maps user-supplied type tokens (upper-cased) to internal type strings
_TYPE_MAP: dict[str, str] = {
    "EPIC":        "epic",
    "EPICS":       "epic",
    "TASK":        "task",
    "TASKS":       "task",
    "SUBTASK":     "child_task",
    "SUBTASKS":    "child_task",
    "CHILD_TASK":  "child_task",
    "CHILD_TASKS": "child_task",
}

_FIELD_MAP: dict[str, str] = {
    "TITLE":       "title",
    "DESCRIPTION": "description",
    "DUEDATE":     "duedate",
    "DUE_DATE":    "duedate",
}


class ParseError(ValueError):
    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos    = 0

    # helpers

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        t = self._tokens[self._pos]
        self._pos += 1
        return t

    def _expect(self, tt: TT) -> Token:
        t = self._advance()
        if t.type != tt:
            raise ParseError(f"Expected {tt.name}, got {t.type.name} ('{t.value}')")
        return t

    # grammar

    def parse(self) -> Query:
        self._expect(TT.FROM)
        types = self._parse_type_list()
        self._expect(TT.SELECT)
        statuses = self._parse_status_list()
        self._expect(TT.WHERE)
        field, op, value = self._parse_condition()
        if self._peek().type != TT.EOF:
            raise ParseError(f"Unexpected token '{self._peek().value}' after WHERE clause")
        return Query(types=types, statuses=statuses, field=field, op=op, value=value)

    def _parse_type_list(self) -> list[str]:
        if self._peek().type == TT.STAR:
            self._advance()
            return ['*']
        seen: set[str] = set()
        seen.add(self._parse_one_type())
        while self._peek().type == TT.COMMA:
            self._advance()
            seen.add(self._parse_one_type())
        return list(seen)

    def _parse_one_type(self) -> str:
        t = self._expect(TT.IDENT)
        normalized = _TYPE_MAP.get(t.value.upper())
        if normalized is None:
            raise ParseError(
                f"Unknown work-item type '{t.value}'. "
                "Expected EPIC, TASK, or SUBTASK (or plural forms)"
            )
        return normalized

    def _parse_status_list(self) -> list[str]:
        if self._peek().type == TT.STAR:
            self._advance()
            return ['*']
        statuses: list[str] = []
        statuses.append(self._parse_one_status())
        while self._peek().type == TT.COMMA:
            self._advance()
            statuses.append(self._parse_one_status())
        return statuses

    def _parse_one_status(self) -> str:
        t = self._peek()
        if t.type in (TT.STRING, TT.IDENT):
            self._advance()
            return _normalize_label(t.value)
        raise ParseError(f"Expected status name, got {t.type.name} ('{t.value}')")

    def _parse_condition(self) -> tuple[str, str, str]:
        field_tok = self._expect(TT.IDENT)
        field = _FIELD_MAP.get(field_tok.value.upper())
        if field is None:
            raise ParseError(
                f"Unknown field '{field_tok.value}'. "
                "Expected TITLE, DESCRIPTION, or DUEDATE"
            )
        op_tok = self._peek()
        if op_tok.type == TT.EQ:
            self._advance()
            op = '='
        elif op_tok.type == TT.CONTAINS:
            self._advance()
            op = '~='
        else:
            raise ParseError(f"Expected '=' or '~=', got '{op_tok.value}'")
        val_tok = self._expect(TT.STRING)
        return field, op, val_tok.value


# ── Normalization helper ──────────────────────────────────────────────────────

def _normalize_label(s: str) -> str:
    """Lowercase and collapse underscores to spaces for status-label comparison."""
    return s.strip().lower().replace('_', ' ')


# ── Evaluator ─────────────────────────────────────────────────────────────────

class WiqlEngine:
    """Parse a WIQL query string and evaluate it against a Board."""

    def evaluate(self, board, query_str: str) -> list:
        """Return the WorkItems from *board* that satisfy *query_str*."""
        tokens = Lexer(query_str).tokenize()
        query  = Parser(tokens).parse()
        return self._run(board, query)

    def _run(self, board, query: Query) -> list:
        items = board.all_items()

        # 1. filter by type
        if query.types != ['*']:
            type_set = set(query.types)
            items = [i for i in items if i.type in type_set]

        # 2. filter by status label (case-insensitive, underscore-tolerant)
        if query.statuses != ['*']:
            wanted = set(query.statuses)  # already normalised
            matching_ids = {
                s.id for s in board.statuses
                if _normalize_label(s.label) in wanted
            }
            items = [i for i in items if i.status_id in matching_ids]

        # 3. filter by field condition
        items = [i for i in items if self._matches(i, query.field, query.op, query.value)]

        return items

    @staticmethod
    def _matches(item, field: str, op: str, value: str) -> bool:
        if field == 'title':
            item_val = item.title
        elif field == 'description':
            item_val = item.description
        elif field == 'duedate':
            item_val = item.due_date.isoformat() if item.due_date else ''
        else:
            return False

        if op == '=':
            return item_val.lower() == value.lower()
        if op == '~=':
            return value.lower() in item_val.lower()
        return False
