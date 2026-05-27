"""Compiler pipeline facade used by GUI and tooling."""

from dataclasses import dataclass
from typing import List

from compiler.errors import Diagnostic, ErrorIntelligenceModule
from compiler.lexer import Token
from compiler.parser import Program
from compiler.semantic import SymbolEntry
from compiler.tac_interpreter import TACInterpreter
from compiler.tac_generator import TACGenerator, TACInstruction


@dataclass(frozen=True)
class CompileOutput:
    """Structured output from a full compiler-core run."""

    tokens: List[Token]
    ast: Program
    symbol_table: List[SymbolEntry]
    tac: List[TACInstruction]
    program_output: List[str]
    diagnostics: List[Diagnostic]


def compile_source(source: str) -> CompileOutput:
    """Run all currently implemented compiler-core phases for a source string."""
    error_module = ErrorIntelligenceModule()
    analysis = error_module.analyze_source(source)
    diagnostics = list(analysis.diagnostics)
    has_frontend_errors = any(d.phase in {"lexical", "syntax"} for d in diagnostics)
    if has_frontend_errors:
        # Prevent noisy cascade diagnostics when parsing/tokenization already failed.
        filtered_diagnostics = [d for d in diagnostics if d.phase in {"lexical", "syntax"}]
        return CompileOutput(
            tokens=analysis.tokens,
            ast=analysis.ast,
            symbol_table=analysis.symbol_table,
            tac=[],
            program_output=[],
            diagnostics=filtered_diagnostics,
        )

    tac = TACGenerator().generate(analysis.ast)
    runtime = TACInterpreter().execute(tac)

    if runtime.runtime_error is not None:
        diagnostics.append(
            Diagnostic(
                phase="runtime",
                severity="error",
                message=runtime.runtime_error,
                suggestion=runtime.runtime_error_suggestion
                or "Review TAC operations and runtime values to fix execution errors.",
                line=runtime.runtime_error_line,
                column=runtime.runtime_error_column,
            )
        )

    return CompileOutput(
        tokens=analysis.tokens,
        ast=analysis.ast,
        symbol_table=analysis.symbol_table,
        tac=tac,
        program_output=runtime.output,
        diagnostics=diagnostics,
    )
