"""Lexical analyzer for EduLang (Phase 2)."""

from dataclasses import dataclass
from typing import List, Tuple


KEYWORDS = {
    "let",
    "if",
    "else",
    "while",
    "print",
    "true",
    "false",
    "int",
    "float",
    "bool",
    "string",
    "array",
    "dict",
}

TWO_CHAR_OPERATORS = {"==", "!=", "<=", ">=", "&&", "||"}
ONE_CHAR_OPERATORS = {"+", "-", "*", "/", "%", "=", "<", ">", "!"}
SYMBOLS = {"(", ")", "{", "}", "[", "]", ";", ":", ","}


@dataclass(frozen=True)
class Token:
    """Represents one lexical token with source position metadata."""

    token_type: str
    lexeme: str
    line: int
    column: int


@dataclass(frozen=True)
class LexerError:
    """Represents a lexical error discovered while scanning input."""

    message: str
    line: int
    column: int


class Lexer:
    """Converts EduLang source text into a token stream and lexical diagnostics."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.length = len(source)
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> Tuple[List[Token], List[LexerError]]:
        tokens: List[Token] = []
        errors: List[LexerError] = []

        while not self._is_at_end():
            ch = self._peek()

            if ch in {" ", "\t", "\r", "\n"}:
                self._consume_whitespace()
                continue

            if ch == "/" and self._peek_next() == "/":
                self._consume_line_comment()
                continue

            if ch == "/" and self._peek_next() == "*":
                if not self._consume_block_comment():
                    errors.append(LexerError("Unterminated block comment", self.line, self.column))
                continue

            start_line, start_col = self.line, self.column

            if ch.isalpha() or ch == "_":
                lexeme = self._consume_identifier()
                token_type = self._classify_identifier_or_keyword(lexeme)
                tokens.append(Token(token_type, lexeme, start_line, start_col))
                continue

            if ch.isdigit():
                number_lexeme, malformed = self._consume_number()
                if malformed:
                    errors.append(
                        LexerError(
                            f"Malformed number literal: {number_lexeme}",
                            start_line,
                            start_col,
                        )
                    )
                else:
                    token_type = "FLOAT_LITERAL" if "." in number_lexeme else "INT_LITERAL"
                    tokens.append(Token(token_type, number_lexeme, start_line, start_col))
                continue

            if ch == '"':
                string_value, terminated = self._consume_string()
                if terminated:
                    tokens.append(Token("STRING_LITERAL", string_value, start_line, start_col))
                else:
                    errors.append(LexerError("Unterminated string literal", start_line, start_col))
                continue

            two_char = ch + self._peek_next()
            if two_char in TWO_CHAR_OPERATORS:
                self._advance()
                self._advance()
                tokens.append(Token("OPERATOR", two_char, start_line, start_col))
                continue

            if ch in ONE_CHAR_OPERATORS:
                self._advance()
                tokens.append(Token("OPERATOR", ch, start_line, start_col))
                continue

            if ch in SYMBOLS:
                self._advance()
                tokens.append(Token("SYMBOL", ch, start_line, start_col))
                continue

            self._advance()
            errors.append(LexerError(f"Invalid character: {ch}", start_line, start_col))

        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens, errors

    def _classify_identifier_or_keyword(self, lexeme: str) -> str:
        if lexeme in {"true", "false"}:
            return "BOOL_LITERAL"
        if lexeme in KEYWORDS:
            return "KEYWORD"
        return "IDENTIFIER"

    def _consume_identifier(self) -> str:
        start = self.index
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        return self.source[start : self.index]

    def _consume_number(self) -> Tuple[str, bool]:
        start = self.index
        has_dot = False
        malformed = False

        while not self._is_at_end():
            ch = self._peek()
            if ch.isdigit():
                self._advance()
            elif ch == ".":
                if has_dot:
                    malformed = True
                    self._advance()
                else:
                    has_dot = True
                    self._advance()
            else:
                break

        return self.source[start : self.index], malformed

    def _consume_string(self) -> Tuple[str, bool]:
        self._advance()  # opening quote
        start = self.index

        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\n":
                return self.source[start : self.index], False
            self._advance()

        if self._is_at_end():
            return self.source[start : self.index], False

        value = self.source[start : self.index]
        self._advance()  # closing quote
        return value, True

    def _consume_whitespace(self) -> None:
        while not self._is_at_end() and self._peek() in {" ", "\t", "\r", "\n"}:
            self._advance()

    def _consume_line_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _consume_block_comment(self) -> bool:
        self._advance()  # /
        self._advance()  # *

        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                return True
            self._advance()

        return False

    def _is_at_end(self) -> bool:
        return self.index >= self.length

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.index]

    def _peek_next(self) -> str:
        if self.index + 1 >= self.length:
            return "\0"
        return self.source[self.index + 1]

    def _advance(self) -> str:
        ch = self.source[self.index]
        self.index += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch
