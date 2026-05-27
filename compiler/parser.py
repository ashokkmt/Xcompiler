"""Syntax analyzer (recursive descent parser) for EduLang (Phase 3)."""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from compiler.lexer import Lexer, Token


@dataclass(frozen=True)
class ParserError:
    """Represents a syntax error with source location and expectation details."""

    message: str
    line: int
    column: int


@dataclass(frozen=True)
class Program:
    statements: List["Statement"]
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class BlockStmt:
    statements: List["Statement"]
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class DeclarationStmt:
    name: str
    var_type: str
    initializer: "Expression"
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class AssignmentStmt:
    name: str
    value: "Expression"
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class PrintStmt:
    expression: "Expression"
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class IfStmt:
    condition: "Expression"
    then_branch: BlockStmt
    else_branch: Optional[BlockStmt]
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class WhileStmt:
    condition: "Expression"
    body: BlockStmt
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class BinaryExpr:
    left: "Expression"
    operator: str
    right: "Expression"
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class UnaryExpr:
    operator: str
    operand: "Expression"
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class LiteralExpr:
    value: Union[int, float, bool, str]
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class IdentifierExpr:
    name: str
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class GroupingExpr:
    expression: "Expression"
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class ArrayLiteralExpr:
    elements: List["Expression"]
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class DictEntryExpr:
    key: "Expression"
    value: "Expression"
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class DictLiteralExpr:
    entries: List[DictEntryExpr]
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class IndexExpr:
    target: "Expression"
    index: "Expression"
    line: int = 0
    column: int = 0


Statement = Union[BlockStmt, DeclarationStmt, AssignmentStmt, PrintStmt, IfStmt, WhileStmt]
Expression = Union[
    BinaryExpr,
    UnaryExpr,
    LiteralExpr,
    IdentifierExpr,
    GroupingExpr,
    ArrayLiteralExpr,
    DictLiteralExpr,
    IndexExpr,
]


class _ParseAbort(Exception):
    """Internal signal used to unwind to statement-level recovery."""


class Parser:
    """Builds an AST from lexer tokens and collects syntax diagnostics."""

    TYPE_KEYWORDS = {"int", "float", "bool", "string", "array", "dict"}
    STATEMENT_START_KEYWORDS = {"let", "print", "if", "while"}

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParserError] = []

    @classmethod
    def from_source(cls, source: str) -> Tuple[Program, List[ParserError], List[str]]:
        """Tokenize and parse source text. Returns AST, parser errors, and lexer error messages."""
        tokens, lex_errors = Lexer(source).tokenize()
        parser = cls(tokens)
        program, parse_errors = parser.parse()
        lex_messages = [f"{e.message} (line {e.line}, col {e.column})" for e in lex_errors]
        return program, parse_errors, lex_messages

    def parse(self) -> Tuple[Program, List[ParserError]]:
        statements: List[Statement] = []

        while not self._is_at_end():
            stmt = self._parse_statement_with_recovery()
            if stmt is not None:
                statements.append(stmt)

        if statements:
            program_line, program_col = self._node_location(statements[0])
        else:
            eof = self._peek()
            program_line, program_col = eof.line, eof.column

        return Program(statements, line=program_line, column=program_col), self.errors

    def _parse_statement_with_recovery(self) -> Optional[Statement]:
        start_index = self.current
        try:
            return self._parse_statement()
        except _ParseAbort:
            self._synchronize()
            # Guarantee forward progress so malformed input cannot trap recovery in a loop.
            if self.current == start_index and not self._is_at_end():
                self._advance()
            return None

    def _parse_statement(self) -> Statement:
        if self._match_keyword("let"):
            return self._parse_declaration_statement()
        if self._match_keyword("print"):
            return self._parse_print_statement()
        if self._match_keyword("if"):
            return self._parse_if_statement()
        if self._match_keyword("while"):
            return self._parse_while_statement()
        if self._match_symbol("{"):
            return self._parse_block_statement()
        if self._check("IDENTIFIER") and self._check_next("OPERATOR", "="):
            return self._parse_assignment_statement()

        token = self._peek()
        self._error(token, "Expected a statement (let, assignment, print, if, while, or block)")
        raise _ParseAbort()

    def _parse_declaration_statement(self) -> DeclarationStmt:
        start_token = self._previous()
        name = self._consume("IDENTIFIER", "Expected variable name after 'let'")
        self._consume_symbol(":", "Expected ':' after variable name")

        type_token = self._consume("KEYWORD", "Expected type keyword after ':'")
        if type_token.lexeme not in self.TYPE_KEYWORDS:
            self._error(type_token, "Expected one of: int, float, bool, string")
            raise _ParseAbort()

        self._consume_operator("=", "Expected '=' after type in declaration")
        initializer = self._parse_expression()
        self._consume_symbol(";", "Expected ';' after declaration")

        return DeclarationStmt(
            name.lexeme,
            type_token.lexeme,
            initializer,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_assignment_statement(self) -> AssignmentStmt:
        name = self._consume("IDENTIFIER", "Expected identifier at start of assignment")
        self._consume_operator("=", "Expected '=' in assignment")
        value = self._parse_expression()
        self._consume_symbol(";", "Expected ';' after assignment")
        return AssignmentStmt(name.lexeme, value, line=name.line, column=name.column)

    def _parse_print_statement(self) -> PrintStmt:
        start_token = self._previous()
        self._consume_symbol("(", "Expected '(' after 'print'")
        expr = self._parse_expression()
        self._consume_symbol(")", "Expected ')' after print expression")
        self._consume_symbol(";", "Expected ';' after print statement")
        return PrintStmt(expr, line=start_token.line, column=start_token.column)

    def _parse_if_statement(self) -> IfStmt:
        start_token = self._previous()
        self._consume_symbol("(", "Expected '(' after 'if'")
        condition = self._parse_expression()
        self._consume_symbol(")", "Expected ')' after if condition")
        then_branch = self._parse_required_block("Expected '{' to start if block")

        else_branch: Optional[BlockStmt] = None
        if self._match_keyword("else"):
            else_branch = self._parse_required_block("Expected '{' to start else block")

        return IfStmt(
            condition,
            then_branch,
            else_branch,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_while_statement(self) -> WhileStmt:
        start_token = self._previous()
        self._consume_symbol("(", "Expected '(' after 'while'")
        condition = self._parse_expression()
        self._consume_symbol(")", "Expected ')' after while condition")
        body = self._parse_required_block("Expected '{' to start while block")
        return WhileStmt(condition, body, line=start_token.line, column=start_token.column)

    def _parse_required_block(self, error_message: str) -> BlockStmt:
        self._consume_symbol("{", error_message)
        return self._parse_block_statement()

    def _parse_block_statement(self) -> BlockStmt:
        start_token = self._previous()
        statements: List[Statement] = []

        while not self._check_symbol("}") and not self._is_at_end():
            stmt = self._parse_statement_with_recovery()
            if stmt is not None:
                statements.append(stmt)

        self._consume_symbol("}", "Expected '}' to close block")
        return BlockStmt(statements, line=start_token.line, column=start_token.column)

    def _parse_expression(self) -> Expression:
        return self._parse_logical_or()

    def _parse_logical_or(self) -> Expression:
        expr = self._parse_logical_and()
        while self._match_operator("||"):
            operator_token = self._previous()
            operator = operator_token.lexeme
            right = self._parse_logical_and()
            expr = BinaryExpr(
                expr,
                operator,
                right,
                line=operator_token.line,
                column=operator_token.column,
            )
        return expr

    def _parse_logical_and(self) -> Expression:
        expr = self._parse_equality()
        while self._match_operator("&&"):
            operator_token = self._previous()
            operator = operator_token.lexeme
            right = self._parse_equality()
            expr = BinaryExpr(
                expr,
                operator,
                right,
                line=operator_token.line,
                column=operator_token.column,
            )
        return expr

    def _parse_equality(self) -> Expression:
        expr = self._parse_comparison()
        while self._match_operator("==", "!="):
            operator_token = self._previous()
            operator = operator_token.lexeme
            right = self._parse_comparison()
            expr = BinaryExpr(
                expr,
                operator,
                right,
                line=operator_token.line,
                column=operator_token.column,
            )
        return expr

    def _parse_comparison(self) -> Expression:
        expr = self._parse_term()
        while self._match_operator("<", "<=", ">", ">="):
            operator_token = self._previous()
            operator = operator_token.lexeme
            right = self._parse_term()
            expr = BinaryExpr(
                expr,
                operator,
                right,
                line=operator_token.line,
                column=operator_token.column,
            )
        return expr

    def _parse_term(self) -> Expression:
        expr = self._parse_factor()
        while self._match_operator("+", "-"):
            operator_token = self._previous()
            operator = operator_token.lexeme
            right = self._parse_factor()
            expr = BinaryExpr(
                expr,
                operator,
                right,
                line=operator_token.line,
                column=operator_token.column,
            )
        return expr

    def _parse_factor(self) -> Expression:
        expr = self._parse_unary()
        while self._match_operator("*", "/", "%"):
            operator_token = self._previous()
            operator = operator_token.lexeme
            right = self._parse_unary()
            expr = BinaryExpr(
                expr,
                operator,
                right,
                line=operator_token.line,
                column=operator_token.column,
            )
        return expr

    def _parse_unary(self) -> Expression:
        if self._match_operator("!", "-"):
            operator_token = self._previous()
            operator = operator_token.lexeme
            operand = self._parse_unary()
            return UnaryExpr(
                operator,
                operand,
                line=operator_token.line,
                column=operator_token.column,
            )
        return self._parse_postfix()

    def _parse_postfix(self) -> Expression:
        expr = self._parse_primary()
        while self._match_symbol("["):
            start_token = self._previous()
            index = self._parse_expression()
            self._consume_symbol("]", "Expected ']' after index expression")
            expr = IndexExpr(expr, index, line=start_token.line, column=start_token.column)
        return expr

    def _parse_primary(self) -> Expression:
        if self._match("INT_LITERAL"):
            token = self._previous()
            return LiteralExpr(int(token.lexeme), line=token.line, column=token.column)
        if self._match("FLOAT_LITERAL"):
            token = self._previous()
            return LiteralExpr(float(token.lexeme), line=token.line, column=token.column)
        if self._match("STRING_LITERAL"):
            token = self._previous()
            return LiteralExpr(token.lexeme, line=token.line, column=token.column)
        if self._match("BOOL_LITERAL"):
            token = self._previous()
            return LiteralExpr(token.lexeme == "true", line=token.line, column=token.column)
        if self._match("IDENTIFIER"):
            token = self._previous()
            return IdentifierExpr(token.lexeme, line=token.line, column=token.column)
        if self._match_symbol("("):
            start_token = self._previous()
            expr = self._parse_expression()
            self._consume_symbol(")", "Expected ')' after grouped expression")
            return GroupingExpr(expr, line=start_token.line, column=start_token.column)
        if self._match_symbol("["):
            return self._parse_array_literal()
        if self._match_symbol("{"):
            return self._parse_dict_literal()

        token = self._peek()
        self._error(token, "Expected expression")
        raise _ParseAbort()

    def _parse_array_literal(self) -> ArrayLiteralExpr:
        start_token = self._previous()
        elements: List[Expression] = []

        if not self._check_symbol("]"):
            elements.append(self._parse_expression())
            while self._match_symbol(","):
                elements.append(self._parse_expression())

        self._consume_symbol("]", "Expected ']' after array literal")
        return ArrayLiteralExpr(elements, line=start_token.line, column=start_token.column)

    def _parse_dict_literal(self) -> DictLiteralExpr:
        start_token = self._previous()
        entries: List[DictEntryExpr] = []

        if not self._check_symbol("}"):
            entries.append(self._parse_dict_entry())
            while self._match_symbol(","):
                entries.append(self._parse_dict_entry())

        self._consume_symbol("}", "Expected '}' after dictionary literal")
        return DictLiteralExpr(entries, line=start_token.line, column=start_token.column)

    def _parse_dict_entry(self) -> DictEntryExpr:
        key_expr = self._parse_expression()
        self._consume_symbol(":", "Expected ':' between dictionary key and value")
        value_expr = self._parse_expression()
        line, column = self._node_location(key_expr)
        return DictEntryExpr(key_expr, value_expr, line=line, column=column)

    def _synchronize(self) -> None:
        while not self._is_at_end():
            if self.current > 0 and self._previous().token_type == "SYMBOL" and self._previous().lexeme == ";":
                return

            if self._check("KEYWORD") and self._peek().lexeme in self.STATEMENT_START_KEYWORDS:
                return

            if self._check_symbol("{") or self._check_symbol("}"):
                return

            self._advance()

    def _consume(self, token_type: str, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        self._error(self._peek(), message)
        raise _ParseAbort()

    def _consume_symbol(self, symbol: str, message: str) -> Token:
        if self._check_symbol(symbol):
            return self._advance()
        self._error(self._peek(), message)
        raise _ParseAbort()

    def _consume_operator(self, operator: str, message: str) -> Token:
        if self._check("OPERATOR") and self._peek().lexeme == operator:
            return self._advance()
        self._error(self._peek(), message)
        raise _ParseAbort()

    def _match(self, token_type: str) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _match_keyword(self, *keywords: str) -> bool:
        if self._check("KEYWORD") and self._peek().lexeme in set(keywords):
            self._advance()
            return True
        return False

    def _match_symbol(self, symbol: str) -> bool:
        if self._check_symbol(symbol):
            self._advance()
            return True
        return False

    def _match_operator(self, *operators: str) -> bool:
        if self._check("OPERATOR") and self._peek().lexeme in set(operators):
            self._advance()
            return True
        return False

    def _check(self, token_type: str) -> bool:
        if self._is_at_end():
            return token_type == "EOF"
        return self._peek().token_type == token_type

    def _check_symbol(self, symbol: str) -> bool:
        return self._check("SYMBOL") and self._peek().lexeme == symbol

    def _check_next(self, token_type: str, lexeme: Optional[str] = None) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        next_token = self.tokens[self.current + 1]
        if next_token.token_type != token_type:
            return False
        if lexeme is not None and next_token.lexeme != lexeme:
            return False
        return True

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().token_type == "EOF"

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> None:
        self.errors.append(ParserError(message, token.line, token.column))

    def _node_location(self, node) -> Tuple[int, int]:
        return getattr(node, "line", 0), getattr(node, "column", 0)
