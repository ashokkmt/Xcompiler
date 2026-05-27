"""Tests for TAC interpreter execution/output generation phase."""

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tac_generator import TACGenerator
from compiler.tac_interpreter import TACInterpreter


def _execute(source: str):
    tokens, lex_errors = Lexer(source).tokenize()
    assert lex_errors == []
    program, parse_errors = Parser(tokens).parse()
    assert parse_errors == []
    tac = TACGenerator().generate(program)
    return TACInterpreter().execute(tac)


def test_executes_arithmetic_and_prints_output():
    result = _execute("let x: int = 1 + 2 * 3; print(x);")

    assert result.runtime_error is None
    assert result.output == ["7"]


def test_executes_while_loop_and_collects_multiple_outputs():
    source = """
    let x: int = 0;
    while (x < 3) {
        print(x);
        x = x + 1;
    }
    """
    result = _execute(source)

    assert result.runtime_error is None
    assert result.output == ["0", "1", "2"]


def test_reports_runtime_error_for_division_by_zero():
    result = _execute("let x: int = 1 / 0; print(x);")

    assert result.runtime_error is not None
    assert "division by zero" in result.runtime_error


def test_executes_array_and_dictionary_index_prints():
    source = '''
    let arr: array = [1, 2, 3];
    let data: dict = {"a": 10, "b": 20};
    print(arr[1]);
    print(data["a"]);
    '''
    result = _execute(source)

    assert result.runtime_error is None
    assert result.output == ["2", "10"]


def test_reports_array_index_out_of_bounds_with_suggestion_and_location():
    result = _execute("let arr: array = [1, 2]; print(arr[5]);")

    assert result.runtime_error is not None
    assert "Array index out of bounds" in result.runtime_error
    assert result.runtime_error_suggestion is not None
    assert "bounds" in result.runtime_error_suggestion.lower()
    assert result.runtime_error_line > 0
    assert result.runtime_error_column > 0


def test_reports_array_index_type_error_with_suggestion_and_location():
    result = _execute('let arr: array = [1, 2]; print(arr["a"]);')

    assert result.runtime_error is not None
    assert "Array index must be integer" in result.runtime_error
    assert result.runtime_error_suggestion is not None
    assert "integer" in result.runtime_error_suggestion.lower()
    assert result.runtime_error_line > 0
    assert result.runtime_error_column > 0


def test_reports_dictionary_key_not_found_with_suggestion_and_location():
    result = _execute('let data: dict = {"a": 1}; print(data["missing"]);')

    assert result.runtime_error is not None
    assert "Dictionary key not found" in result.runtime_error
    assert result.runtime_error_suggestion is not None
    assert "key" in result.runtime_error_suggestion.lower()
    assert result.runtime_error_line > 0
    assert result.runtime_error_column > 0


def test_reports_invalid_dictionary_key_access_with_suggestion_and_location():
    result = _execute('let data: dict = {"a": 1}; print(data[[1]]);')

    assert result.runtime_error is not None
    assert "Invalid dictionary key access" in result.runtime_error
    assert result.runtime_error_suggestion is not None
    assert "hashable" in result.runtime_error_suggestion.lower()
    assert result.runtime_error_line > 0
    assert result.runtime_error_column > 0
