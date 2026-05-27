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


def test_compile_source_stops_after_syntax_errors_for_invalid_dict_literal():
    source = '''
    let data: dict = {"a" 10, "b": 20};
    print(data["a"]);
    '''

    result = compile_source(source)

    assert len(result.diagnostics) >= 1
    assert any(d.phase == "syntax" for d in result.diagnostics)
    assert all(d.phase in {"lexical", "syntax"} for d in result.diagnostics)
    assert result.tac == []
    assert result.program_output == []


def test_compile_source_runtime_diagnostic_has_location_and_suggestion():
    source = "let arr: array = [1]; print(arr[2]);"

    result = compile_source(source)

    runtime_errors = [d for d in result.diagnostics if d.phase == "runtime"]
    assert len(runtime_errors) == 1

    runtime_error = runtime_errors[0]
    assert "Array index out of bounds" in runtime_error.message
    assert runtime_error.suggestion
    assert runtime_error.line > 0
    assert runtime_error.column > 0
