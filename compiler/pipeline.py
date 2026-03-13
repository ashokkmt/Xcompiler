"""Compiler pipeline facade used by GUI and tooling."""

from dataclasses import dataclass
from typing import List

from compiler.errors import Diagnostic, ErrorIntelligenceModule
from compiler.lexer import Token
from compiler.parser import Program
from compiler.semantic import SymbolEntry
from compiler.tac_generator import TACGenerator, TACInstruction


@dataclass(frozen=True)
class CompileOutput:
    """Structured output from a full compiler-core run."""

    tokens: List[Token]
    ast: Program
    symbol_table: List[SymbolEntry]
    tac: List[TACInstruction]
    diagnostics: List[Diagnostic]


def compile_source(source: str) -> CompileOutput:
    """Run all currently implemented compiler-core phases for a source string."""
    error_module = ErrorIntelligenceModule()
    analysis = error_module.analyze_source(source)
    tac = TACGenerator().generate(analysis.ast)

    return CompileOutput(
        tokens=analysis.tokens,
        ast=analysis.ast,
        symbol_table=analysis.symbol_table,
        tac=tac,
        diagnostics=analysis.diagnostics,
    )
