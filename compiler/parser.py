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


@dataclass(frozen=True)
class BlockStmt:
    statements: List["Statement"]


@dataclass(frozen=True)
class DeclarationStmt:
    name: str
    var_type: str
    initializer: "Expression"


@dataclass(frozen=True)
class AssignmentStmt:
    name: str
    value: "Expression"


@dataclass(frozen=True)
class PrintStmt:
    expression: "Expression"


@dataclass(frozen=True)
class IfStmt:
    condition: "Expression"
    then_branch: BlockStmt
    else_branch: Optional[BlockStmt]


@dataclass(frozen=True)
class WhileStmt:
    condition: "Expression"
    body: BlockStmt


@dataclass(frozen=True)
class BinaryExpr:
    left: "Expression"
    operator: str
    right: "Expression"


@dataclass(frozen=True)
class UnaryExpr:
    operator: str
    operand: "Expression"


@dataclass(frozen=True)
class LiteralExpr:
    value: Union[int, float, bool, str]


@dataclass(frozen=True)
class IdentifierExpr:
    name: str


@dataclass(frozen=True)
class GroupingExpr:
    expression: "Expression"


Statement = Union[BlockStmt, DeclarationStmt, AssignmentStmt, PrintStmt, IfStmt, WhileStmt]
Expression = Union[BinaryExpr, UnaryExpr, LiteralExpr, IdentifierExpr, GroupingExpr]


class _ParseAbort(Exception):
    """Internal signal used to unwind to statement-level recovery."""


class Parser:
    """Builds an AST from lexer tokens and collects syntax diagnostics."""

    TYPE_KEYWORDS = {"int", "float", "bool", "string"}
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

        return Program(statements), self.errors

    def _parse_statement_with_recovery(self) -> Optional[Statement]:
        try:
            return self._parse_statement()
        except _ParseAbort:
            self._synchronize()
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
        name = self._consume("IDENTIFIER", "Expected variable name after 'let'")
        self._consume_symbol(":", "Expected ':' after variable name")

        type_token = self._consume("KEYWORD", "Expected type keyword after ':'")
        if type_token.lexeme not in self.TYPE_KEYWORDS:
            self._error(type_token, "Expected one of: int, float, bool, string")
            raise _ParseAbort()

        self._consume_operator("=", "Expected '=' after type in declaration")
        initializer = self._parse_expression()
        self._consume_symbol(";", "Expected ';' after declaration")

        return DeclarationStmt(name.lexeme, type_token.lexeme, initializer)

    def _parse_assignment_statement(self) -> AssignmentStmt:
        name = self._consume("IDENTIFIER", "Expected identifier at start of assignment")
        self._consume_operator("=", "Expected '=' in assignment")
        value = self._parse_expression()
        self._consume_symbol(";", "Expected ';' after assignment")
        return AssignmentStmt(name.lexeme, value)

    def _parse_print_statement(self) -> PrintStmt:
        self._consume_symbol("(", "Expected '(' after 'print'")
        expr = self._parse_expression()
        self._consume_symbol(")", "Expected ')' after print expression")
        self._consume_symbol(";", "Expected ';' after print statement")
        return PrintStmt(expr)

    def _parse_if_statement(self) -> IfStmt:
        self._consume_symbol("(", "Expected '(' after 'if'")
        condition = self._parse_expression()
        self._consume_symbol(")", "Expected ')' after if condition")
        then_branch = self._parse_required_block("Expected '{' to start if block")

        else_branch: Optional[BlockStmt] = None
        if self._match_keyword("else"):
            else_branch = self._parse_required_block("Expected '{' to start else block")

        return IfStmt(condition, then_branch, else_branch)

    def _parse_while_statement(self) -> WhileStmt:
        self._consume_symbol("(", "Expected '(' after 'while'")
        condition = self._parse_expression()
        self._consume_symbol(")", "Expected ')' after while condition")
        body = self._parse_required_block("Expected '{' to start while block")
        return WhileStmt(condition, body)

    def _parse_required_block(self, error_message: str) -> BlockStmt:
        self._consume_symbol("{", error_message)
        return self._parse_block_statement()

    def _parse_block_statement(self) -> BlockStmt:
        statements: List[Statement] = []

        while not self._check_symbol("}") and not self._is_at_end():
            stmt = self._parse_statement_with_recovery()
            if stmt is not None:
                statements.append(stmt)

        self._consume_symbol("}", "Expected '}' to close block")
        return BlockStmt(statements)

    def _parse_expression(self) -> Expression:
        return self._parse_logical_or()

    def _parse_logical_or(self) -> Expression:
        expr = self._parse_logical_and()
        while self._match_operator("||"):
            operator = self._previous().lexeme
            right = self._parse_logical_and()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def _parse_logical_and(self) -> Expression:
        expr = self._parse_equality()
        while self._match_operator("&&"):
            operator = self._previous().lexeme
            right = self._parse_equality()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def _parse_equality(self) -> Expression:
        expr = self._parse_comparison()
        while self._match_operator("==", "!="):
            operator = self._previous().lexeme
            right = self._parse_comparison()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def _parse_comparison(self) -> Expression:
        expr = self._parse_term()
        while self._match_operator("<", "<=", ">", ">="):
            operator = self._previous().lexeme
            right = self._parse_term()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def _parse_term(self) -> Expression:
        expr = self._parse_factor()
        while self._match_operator("+", "-"):
            operator = self._previous().lexeme
            right = self._parse_factor()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def _parse_factor(self) -> Expression:
        expr = self._parse_unary()
        while self._match_operator("*", "/", "%"):
            operator = self._previous().lexeme
            right = self._parse_unary()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def _parse_unary(self) -> Expression:
        if self._match_operator("!", "-"):
            operator = self._previous().lexeme
            operand = self._parse_unary()
            return UnaryExpr(operator, operand)
        return self._parse_primary()

    def _parse_primary(self) -> Expression:
        if self._match("INT_LITERAL"):
            return LiteralExpr(int(self._previous().lexeme))
        if self._match("FLOAT_LITERAL"):
            return LiteralExpr(float(self._previous().lexeme))
        if self._match("STRING_LITERAL"):
            return LiteralExpr(self._previous().lexeme)
        if self._match("BOOL_LITERAL"):
            return LiteralExpr(self._previous().lexeme == "true")
        if self._match("IDENTIFIER"):
            return IdentifierExpr(self._previous().lexeme)
        if self._match_symbol("("):
            expr = self._parse_expression()
            self._consume_symbol(")", "Expected ')' after grouped expression")
            return GroupingExpr(expr)

        token = self._peek()
        self._error(token, "Expected expression")
        raise _ParseAbort()

    def _synchronize(self) -> None:
        while not self._is_at_end():
            if self._previous().token_type == "SYMBOL" and self._previous().lexeme == ";":
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
