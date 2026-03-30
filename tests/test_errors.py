"""Phase 6 tests for error detection and suggestion module."""

from compiler.errors import ErrorIntelligenceModule
from compiler.lexer import LexerError
from compiler.parser import ParserError
from compiler.semantic import SemanticError


def test_collect_builds_unified_diagnostics_with_suggestions():
    module = ErrorIntelligenceModule()

    diagnostics = module.collect(
        lexer_errors=[LexerError("Unterminated string literal", 2, 5)],
        parser_errors=[ParserError("Expected ';' after declaration", 3, 10)],
        semantic_errors=[SemanticError("Use of undeclared variable 'x'", 4, 1)],
    )

    assert len(diagnostics) == 3
    assert diagnostics[0].phase == "lexical"
    assert diagnostics[1].phase == "syntax"
    assert diagnostics[2].phase == "semantic"
    assert all(d.suggestion for d in diagnostics)


def test_analyze_source_recovers_and_reports_multiple_phases():
    module = ErrorIntelligenceModule()
    source = """
    let x: int = 1
    print(x);
    y = x + 1;
    """

    result = module.analyze_source(source)

    assert len(result.tokens) > 0
    assert len(result.ast.statements) >= 1
    assert len(result.diagnostics) >= 2
    messages = [d.message for d in result.diagnostics]
    assert any("Expected ';' after declaration" in m for m in messages)
    assert any("Use of undeclared variable 'y'" in m for m in messages)


def test_diagnostics_are_sorted_by_location_and_phase_tiebreaker():
    module = ErrorIntelligenceModule()

    diagnostics = module.collect(
        lexer_errors=[LexerError("Invalid character: @", 5, 2)],
        parser_errors=[ParserError("Expected expression", 2, 8)],
        semantic_errors=[SemanticError("Type mismatch in assignment to 'a': expected int, got string", 2, 8)],
    )

    assert diagnostics[0].line == 2
    assert diagnostics[0].phase == "syntax"
    assert diagnostics[1].line == 2
    assert diagnostics[1].phase == "semantic"
    assert diagnostics[2].line == 5


def test_suggestion_engine_handles_common_patterns():
    module = ErrorIntelligenceModule()

    diagnostics = module.collect(
        lexer_errors=[],
        parser_errors=[ParserError("Expected ')' after if condition", 1, 1)],
        semantic_errors=[SemanticError("While condition must be of type bool", 0, 0)],
    )

    suggestions = [d.suggestion for d in diagnostics]
    assert any("parentheses" in s.lower() for s in suggestions)
    assert any("boolean expression" in s.lower() for s in suggestions)


def test_collect_compacts_adjacent_duplicate_statement_recovery_errors():
    module = ErrorIntelligenceModule()

    diagnostics = module.collect(
        lexer_errors=[],
        parser_errors=[
            ParserError("Expected ':' between dictionary key and value", 2, 23),
            ParserError("Expected a statement (let, assignment, print, if, while, or block)", 2, 34),
            ParserError("Expected a statement (let, assignment, print, if, while, or block)", 2, 35),
        ],
        semantic_errors=[],
    )

    assert len(diagnostics) == 2
    assert diagnostics[0].message == "Expected ':' between dictionary key and value"
    assert diagnostics[1].message == "Expected a statement (let, assignment, print, if, while, or block)"
