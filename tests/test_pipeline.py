"""Phase 7 tests for compiler pipeline facade used by GUI."""

from compiler.pipeline import compile_source


def test_compile_source_returns_all_sections_for_valid_code():
    source = """
    let x: int = 1;
    print(x);
    """
    result = compile_source(source)

    assert len(result.tokens) > 0
    assert len(result.ast.statements) >= 1
    assert len(result.symbol_table) >= 1
    assert len(result.tac) >= 1
    assert result.program_output == ["1"]
    assert result.diagnostics == []


def test_compile_source_returns_diagnostics_for_invalid_code():
    source = """
    let x: int =
    y = x + 1;
    """
    result = compile_source(source)

    assert len(result.tokens) > 0
    assert isinstance(result.program_output, list)
    assert len(result.diagnostics) >= 1
    assert any(d.phase in {"syntax", "semantic"} for d in result.diagnostics)
