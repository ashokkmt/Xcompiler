"""Error detection and suggestion module for EduLang (Phase 6)."""

from dataclasses import dataclass
from typing import Iterable, List, Literal, Optional, Tuple

from compiler.lexer import Lexer, LexerError, Token
from compiler.parser import Parser, ParserError, Program
from compiler.semantic import SemanticAnalyzer, SemanticError, SymbolEntry

PhaseName = Literal["lexical", "syntax", "semantic", "runtime"]
Severity = Literal["error", "warning", "hint"]


@dataclass(frozen=True)
class Diagnostic:
    """Unified diagnostic model used by the error intelligence module."""

    phase: PhaseName
    severity: Severity
    message: str
    suggestion: str
    line: int
    column: int


@dataclass(frozen=True)
class AnalysisResult:
    """Result bundle for recovery-oriented source analysis."""

    tokens: List[Token]
    ast: Program
    symbol_table: List[SymbolEntry]
    diagnostics: List[Diagnostic]


class ErrorIntelligenceModule:
    """Aggregates phase errors and enriches them with correction hints."""

    def collect(
        self,
        lexer_errors: Iterable[LexerError],
        parser_errors: Iterable[ParserError],
        semantic_errors: Iterable[SemanticError],
    ) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        for error in lexer_errors:
            diagnostics.append(
                Diagnostic(
                    phase="lexical",
                    severity="error",
                    message=error.message,
                    suggestion=self._suggest(error.message),
                    line=error.line,
                    column=error.column,
                )
            )

        for error in parser_errors:
            diagnostics.append(
                Diagnostic(
                    phase="syntax",
                    severity="error",
                    message=error.message,
                    suggestion=self._suggest(error.message),
                    line=error.line,
                    column=error.column,
                )
            )

        for error in semantic_errors:
            diagnostics.append(
                Diagnostic(
                    phase="semantic",
                    severity="error",
                    message=error.message,
                    suggestion=self._suggest(error.message),
                    line=error.line,
                    column=error.column,
                )
            )

        diagnostics.sort(key=self._sort_key)
        return diagnostics

    def analyze_source(self, source: str) -> AnalysisResult:
        """Run lexer, parser, and semantic analysis with basic recovery behavior."""
        tokens, lexer_errors = Lexer(source).tokenize()
        ast, parser_errors = Parser(tokens).parse()
        symbols, semantic_errors = SemanticAnalyzer().analyze(ast)

        diagnostics = self.collect(lexer_errors, parser_errors, semantic_errors)
        return AnalysisResult(tokens=tokens, ast=ast, symbol_table=symbols, diagnostics=diagnostics)

    def _sort_key(self, diagnostic: Diagnostic) -> Tuple[int, int, int]:
        # Use phase order as a stable tie-breaker for same source location.
        phase_order = {"lexical": 0, "syntax": 1, "semantic": 2, "runtime": 3}
        line = diagnostic.line if diagnostic.line > 0 else 10**9
        col = diagnostic.column if diagnostic.column > 0 else 10**9
        return (line, col, phase_order[diagnostic.phase])

    def _suggest(self, message: str) -> str:
        lowered = message.lower()

        if "missing" in lowered and "semicolon" in lowered:
            return "Add a semicolon ';' at the end of the statement."

        if "expected ';'" in lowered:
            return "Add a semicolon ';' to complete the statement."

        if "expected ')'" in lowered or "expected '('" in lowered:
            return "Check parentheses pairing in this expression or statement."

        if "expected '}'" in lowered or "start" in lowered and "block" in lowered:
            return "Ensure block braces '{' and '}' are correctly matched."

        if "invalid character" in lowered:
            return "Remove unsupported characters or replace them with valid language symbols."

        if "unterminated string" in lowered:
            return "Close the string literal with a matching double quote."

        if "unterminated block comment" in lowered:
            return "Close the block comment with '*/'."

        if "malformed number literal" in lowered:
            return "Use a valid numeric format such as 10, 3.14, or 0.5."

        if "undeclared variable" in lowered:
            return "Declare the variable with 'let <name>: <type> = <value>;' before using it."

        if "redeclaration" in lowered:
            return "Rename the variable or remove the duplicate declaration in the same scope."

        if "type mismatch" in lowered:
            return "Adjust the expression so its type matches the target variable type."

        if "condition must be of type bool" in lowered:
            return "Use a boolean expression (for example: x < 10 or a && b) in the condition."

        if "expected expression" in lowered:
            return "Provide a valid expression at this position."

        if "expected a statement" in lowered:
            return "Start with a valid statement such as let, assignment, print, if, while, or block."

        return "Review the syntax near this location and compare with language grammar rules."
