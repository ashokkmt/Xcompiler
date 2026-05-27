"""Intermediate Code Generator (Three-Address Code) for EduLang (Phase 5)."""

from dataclasses import dataclass
from typing import List, Optional

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


@dataclass(frozen=True)
class TACInstruction:
    """Represents one TAC instruction."""

    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    line: int = 0
    column: int = 0


class TACGenerator:
    """Converts AST statements and expressions into linear TAC instructions."""

    def __init__(self) -> None:
        self.instructions: List[TACInstruction] = []
        self._temp_index = 0
        self._label_index = 0

    def generate(self, program: Program) -> List[TACInstruction]:
        """Generate TAC for a parsed program."""
        self.instructions = []
        self._temp_index = 0
        self._label_index = 0

        for statement in program.statements:
            self._emit_statement(statement)

        return self.instructions

    def _emit_statement(self, statement: Statement) -> None:
        if isinstance(statement, DeclarationStmt):
            value = self._emit_expression(statement.initializer)
            self.instructions.append(
                TACInstruction(
                    "ASSIGN",
                    value,
                    None,
                    statement.name,
                    line=statement.line,
                    column=statement.column,
                )
            )
            return

        if isinstance(statement, AssignmentStmt):
            value = self._emit_expression(statement.value)
            self.instructions.append(
                TACInstruction(
                    "ASSIGN",
                    value,
                    None,
                    statement.name,
                    line=statement.line,
                    column=statement.column,
                )
            )
            return

        if isinstance(statement, PrintStmt):
            value = self._emit_expression(statement.expression)
            self.instructions.append(
                TACInstruction("PRINT", value, line=statement.line, column=statement.column)
            )
            return

        if isinstance(statement, IfStmt):
            self._emit_if(statement)
            return

        if isinstance(statement, WhileStmt):
            self._emit_while(statement)
            return

        if isinstance(statement, BlockStmt):
            for inner in statement.statements:
                self._emit_statement(inner)
            return

    def _emit_if(self, statement: IfStmt) -> None:
        condition = self._emit_expression(statement.condition)
        else_label = self._new_label()
        end_label = self._new_label()

        self.instructions.append(
            TACInstruction(
                "IF_FALSE_GOTO",
                condition,
                None,
                else_label,
                line=statement.line,
                column=statement.column,
            )
        )

        for inner in statement.then_branch.statements:
            self._emit_statement(inner)

        self.instructions.append(
            TACInstruction(
                "GOTO",
                None,
                None,
                end_label,
                line=statement.line,
                column=statement.column,
            )
        )
        self.instructions.append(
            TACInstruction(
                "LABEL",
                None,
                None,
                else_label,
                line=statement.line,
                column=statement.column,
            )
        )

        if statement.else_branch is not None:
            for inner in statement.else_branch.statements:
                self._emit_statement(inner)

        self.instructions.append(
            TACInstruction(
                "LABEL",
                None,
                None,
                end_label,
                line=statement.line,
                column=statement.column,
            )
        )

    def _emit_while(self, statement: WhileStmt) -> None:
        start_label = self._new_label()
        end_label = self._new_label()

        self.instructions.append(
            TACInstruction(
                "LABEL",
                None,
                None,
                start_label,
                line=statement.line,
                column=statement.column,
            )
        )

        condition = self._emit_expression(statement.condition)
        self.instructions.append(
            TACInstruction(
                "IF_FALSE_GOTO",
                condition,
                None,
                end_label,
                line=statement.line,
                column=statement.column,
            )
        )

        for inner in statement.body.statements:
            self._emit_statement(inner)

        self.instructions.append(
            TACInstruction(
                "GOTO",
                None,
                None,
                start_label,
                line=statement.line,
                column=statement.column,
            )
        )
        self.instructions.append(
            TACInstruction(
                "LABEL",
                None,
                None,
                end_label,
                line=statement.line,
                column=statement.column,
            )
        )

    def _emit_expression(self, expression) -> str:
        if isinstance(expression, LiteralExpr):
            return self._literal_to_operand(expression.value)

        if isinstance(expression, IdentifierExpr):
            return expression.name

        if isinstance(expression, GroupingExpr):
            return self._emit_expression(expression.expression)

        if isinstance(expression, ArrayLiteralExpr):
            target = self._new_temp()
            self.instructions.append(
                TACInstruction(
                    "ARRAY_NEW",
                    None,
                    None,
                    target,
                    line=expression.line,
                    column=expression.column,
                )
            )
            for element in expression.elements:
                value = self._emit_expression(element)
                self.instructions.append(
                    TACInstruction(
                        "ARRAY_APPEND",
                        target,
                        value,
                        target,
                        line=element.line,
                        column=element.column,
                    )
                )
            return target

        if isinstance(expression, DictLiteralExpr):
            target = self._new_temp()
            self.instructions.append(
                TACInstruction(
                    "DICT_NEW",
                    None,
                    None,
                    target,
                    line=expression.line,
                    column=expression.column,
                )
            )
            for entry in expression.entries:
                key = self._emit_expression(entry.key)
                value = self._emit_expression(entry.value)
                self.instructions.append(
                    TACInstruction(
                        "DICT_SET",
                        key,
                        value,
                        target,
                        line=entry.line,
                        column=entry.column,
                    )
                )
            return target

        if isinstance(expression, IndexExpr):
            target = self._new_temp()
            collection = self._emit_expression(expression.target)
            index = self._emit_expression(expression.index)
            self.instructions.append(
                TACInstruction(
                    "INDEX_GET",
                    collection,
                    index,
                    target,
                    line=expression.line,
                    column=expression.column,
                )
            )
            return target

        if isinstance(expression, UnaryExpr):
            operand = self._emit_expression(expression.operand)
            target = self._new_temp()
            op = "NEG" if expression.operator == "-" else "NOT"
            self.instructions.append(
                TACInstruction(
                    op,
                    operand,
                    None,
                    target,
                    line=expression.line,
                    column=expression.column,
                )
            )
            return target

        if isinstance(expression, BinaryExpr):
            left = self._emit_expression(expression.left)
            right = self._emit_expression(expression.right)
            target = self._new_temp()
            self.instructions.append(
                TACInstruction(
                    expression.operator,
                    left,
                    right,
                    target,
                    line=expression.line,
                    column=expression.column,
                )
            )
            return target

        raise ValueError("Unsupported expression node for TAC generation")

    def _new_temp(self) -> str:
        self._temp_index += 1
        return f"t{self._temp_index}"

    def _new_label(self) -> str:
        self._label_index += 1
        return f"L{self._label_index}"

    def _literal_to_operand(self, value) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)
