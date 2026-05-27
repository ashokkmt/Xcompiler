"""Semantic analyzer for EduLang (Phase 4)."""

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

from compiler.parser import (
    ArrayLiteralExpr,
    AssignmentStmt,
    BinaryExpr,
    BlockStmt,
    DeclarationStmt,
    DictLiteralExpr,
    GroupingExpr,
    IdentifierExpr,
    IndexExpr,
    IfStmt,
    LiteralExpr,
    PrintStmt,
    Program,
    Statement,
    UnaryExpr,
    WhileStmt,
)

TypeName = Literal["int", "float", "bool", "string", "array", "dict", "any", "error"]


@dataclass(frozen=True)
class SemanticError:
    """Represents a semantic error identified during AST validation."""

    message: str
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class SymbolEntry:
    """Represents one declared symbol in a specific scope."""

    name: str
    var_type: str
    scope_level: int


class SemanticAnalyzer:
    """Performs scope and type validation over parser AST output."""

    def __init__(self) -> None:
        self._scopes: List[Dict[str, str]] = [{}]
        self._errors: List[SemanticError] = []
        self._symbols: List[SymbolEntry] = []

    def analyze(self, program: Program) -> Tuple[List[SymbolEntry], List[SemanticError]]:
        """Analyze the AST and return symbol table entries plus diagnostics."""
        self._scopes = [{}]
        self._errors = []
        self._symbols = []

        for statement in program.statements:
            self._analyze_statement(statement)

        return self._symbols, self._errors

    def _analyze_statement(self, statement: Statement) -> None:
        if isinstance(statement, DeclarationStmt):
            self._analyze_declaration(statement)
            return
        if isinstance(statement, AssignmentStmt):
            self._analyze_assignment(statement)
            return
        if isinstance(statement, PrintStmt):
            self._infer_expression_type(statement.expression)
            return
        if isinstance(statement, IfStmt):
            condition_type = self._infer_expression_type(statement.condition)
            if condition_type != "bool" and condition_type != "error":
                self._error(
                    "If condition must be of type bool",
                    statement.condition.line,
                    statement.condition.column,
                )
            self._analyze_block(statement.then_branch)
            if statement.else_branch is not None:
                self._analyze_block(statement.else_branch)
            return
        if isinstance(statement, WhileStmt):
            condition_type = self._infer_expression_type(statement.condition)
            if condition_type != "bool" and condition_type != "error":
                self._error(
                    "While condition must be of type bool",
                    statement.condition.line,
                    statement.condition.column,
                )
            self._analyze_block(statement.body)
            return
        if isinstance(statement, BlockStmt):
            self._analyze_block(statement)
            return

    def _analyze_block(self, block: BlockStmt) -> None:
        self._enter_scope()
        for statement in block.statements:
            self._analyze_statement(statement)
        self._exit_scope()

    def _analyze_declaration(self, statement: DeclarationStmt) -> None:
        current_scope = self._scopes[-1]
        if statement.name in current_scope:
            self._error(
                f"Redeclaration of variable '{statement.name}' in the same scope",
                statement.line,
                statement.column,
            )
            return

        value_type = self._infer_expression_type(statement.initializer)
        if not self._is_assignable(statement.var_type, value_type):
            self._error(
                f"Type mismatch in declaration of '{statement.name}': "
                f"expected {statement.var_type}, got {value_type}",
                statement.line,
                statement.column,
            )

        current_scope[statement.name] = statement.var_type
        self._symbols.append(SymbolEntry(statement.name, statement.var_type, self._scope_level))

    def _analyze_assignment(self, statement: AssignmentStmt) -> None:
        target_type = self._lookup(statement.name)
        if target_type is None:
            self._error(
                f"Use of undeclared variable '{statement.name}'",
                statement.line,
                statement.column,
            )
            self._infer_expression_type(statement.value)
            return

        value_type = self._infer_expression_type(statement.value)
        if not self._is_assignable(target_type, value_type):
            self._error(
                f"Type mismatch in assignment to '{statement.name}': "
                f"expected {target_type}, got {value_type}",
                statement.line,
                statement.column,
            )

    def _infer_expression_type(self, expr) -> TypeName:
        if isinstance(expr, LiteralExpr):
            value = expr.value
            if isinstance(value, bool):
                return "bool"
            if isinstance(value, int):
                return "int"
            if isinstance(value, float):
                return "float"
            if isinstance(value, str):
                return "string"
            return "error"

        if isinstance(expr, IdentifierExpr):
            found = self._lookup(expr.name)
            if found is None:
                self._error(
                    f"Use of undeclared variable '{expr.name}'",
                    expr.line,
                    expr.column,
                )
                return "error"
            return found  # type: ignore[return-value]

        if isinstance(expr, GroupingExpr):
            return self._infer_expression_type(expr.expression)

        if isinstance(expr, ArrayLiteralExpr):
            element_types: List[TypeName] = []
            for element in expr.elements:
                element_types.append(self._infer_expression_type(element))

            non_error_types = {t for t in element_types if t != "error"}
            if len(non_error_types) > 1:
                self._error(
                    "Array literal elements must all have the same type",
                    expr.line,
                    expr.column,
                )
                return "error"

            return "array"

        if isinstance(expr, DictLiteralExpr):
            key_types: List[TypeName] = []
            for entry in expr.entries:
                key_types.append(self._infer_expression_type(entry.key))
                self._infer_expression_type(entry.value)

            non_error_key_types = {t for t in key_types if t != "error"}
            if len(non_error_key_types) > 1:
                self._error(
                    "Dictionary literal keys must all have the same type",
                    expr.line,
                    expr.column,
                )
                return "error"

            return "dict"

        if isinstance(expr, IndexExpr):
            target_type = self._infer_expression_type(expr.target)
            index_type = self._infer_expression_type(expr.index)
            if target_type == "array":
                if index_type not in {"int", "error"}:
                    self._error(
                        "Array indexing requires int index",
                        expr.index.line,
                        expr.index.column,
                    )
                    return "error"
                return "any"
            if target_type == "dict":
                return "any"
            if target_type != "error":
                self._error(
                    "Indexing requires array or dict target",
                    expr.line,
                    expr.column,
                )
            return "error"

        if isinstance(expr, UnaryExpr):
            operand_type = self._infer_expression_type(expr.operand)
            if expr.operator == "!":
                if operand_type == "any":
                    return "bool"
                if operand_type != "bool" and operand_type != "error":
                    self._error(
                        "Logical '!' operator requires bool operand",
                        expr.line,
                        expr.column,
                    )
                    return "error"
                return "bool"
            if expr.operator == "-":
                if operand_type == "any":
                    return "any"
                if operand_type not in {"int", "float", "error"}:
                    self._error(
                        "Unary '-' operator requires numeric operand",
                        expr.line,
                        expr.column,
                    )
                    return "error"
                return operand_type
            self._error(
                f"Unsupported unary operator '{expr.operator}'",
                expr.line,
                expr.column,
            )
            return "error"

        if isinstance(expr, BinaryExpr):
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)
            op = expr.operator

            if op in {"+", "-", "*", "/"}:
                if "any" in {left_type, right_type}:
                    return "any"
                if self._is_numeric(left_type) and self._is_numeric(right_type):
                    if op == "/":
                        return "float"
                    if "float" in {left_type, right_type}:
                        return "float"
                    return "int"
                if left_type != "error" and right_type != "error":
                    self._error(
                        f"Operator '{op}' requires numeric operands",
                        expr.line,
                        expr.column,
                    )
                return "error"

            if op == "%":
                if "any" in {left_type, right_type}:
                    return "any"
                if left_type == "int" and right_type == "int":
                    return "int"
                if left_type != "error" and right_type != "error":
                    self._error("Operator '%' requires int operands", expr.line, expr.column)
                return "error"

            if op in {"<", "<=", ">", ">="}:
                if "any" in {left_type, right_type}:
                    return "bool"
                if self._is_numeric(left_type) and self._is_numeric(right_type):
                    return "bool"
                if left_type != "error" and right_type != "error":
                    self._error(
                        f"Operator '{op}' requires numeric operands",
                        expr.line,
                        expr.column,
                    )
                return "error"

            if op in {"==", "!="}:
                if self._types_compatible(left_type, right_type):
                    return "bool"
                if left_type != "error" and right_type != "error":
                    self._error(
                        f"Cannot compare incompatible types: {left_type} and {right_type}",
                        expr.line,
                        expr.column,
                    )
                return "error"

            if op in {"&&", "||"}:
                if "any" in {left_type, right_type}:
                    return "bool"
                if left_type == "bool" and right_type == "bool":
                    return "bool"
                if left_type != "error" and right_type != "error":
                    self._error(
                        f"Operator '{op}' requires bool operands",
                        expr.line,
                        expr.column,
                    )
                return "error"

            self._error(f"Unsupported binary operator '{op}'", expr.line, expr.column)
            return "error"

        self._error("Unsupported expression node", getattr(expr, "line", 0), getattr(expr, "column", 0))
        return "error"

    def _is_numeric(self, type_name: TypeName) -> bool:
        return type_name in {"int", "float"}

    def _types_compatible(self, left: TypeName, right: TypeName) -> bool:
        if "error" in {left, right}:
            return True
        if "any" in {left, right}:
            return True
        if left == right:
            return True
        return {left, right} == {"int", "float"}

    def _is_assignable(self, target: str, source: TypeName) -> bool:
        if source == "error":
            return True
        if source == "any":
            return True
        if target == source:
            return True
        return target == "float" and source == "int"

    @property
    def _scope_level(self) -> int:
        return len(self._scopes) - 1

    def _lookup(self, name: str):
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def _enter_scope(self) -> None:
        self._scopes.append({})

    def _exit_scope(self) -> None:
        self._scopes.pop()

    def _error(self, message: str, line: int = 0, column: int = 0) -> None:
        self._errors.append(SemanticError(message, line, column))
