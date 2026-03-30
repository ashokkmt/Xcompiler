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
