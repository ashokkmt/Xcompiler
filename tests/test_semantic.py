"""Phase 4 tests for EduLang semantic analyzer."""

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer


def _analyze(source: str):
    tokens, lex_errors = Lexer(source).tokenize()
    assert lex_errors == []

    program, parse_errors = Parser(tokens).parse()
    assert parse_errors == []

    return SemanticAnalyzer().analyze(program)


def test_valid_program_has_no_semantic_errors():
    source = """
    let x: int = 1;
    let y: float = x + 2.5;
    if (x < 10) {
        let msg: string = "ok";
        print(msg);
    }
    x = x + 1;
    """
    symbols, errors = _analyze(source)

    assert errors == []
    names = [s.name for s in symbols]
    assert "x" in names
    assert "y" in names


def test_reports_undeclared_variable_use():
    source = "let x: int = y + 1;"
    _symbols, errors = _analyze(source)

    assert len(errors) >= 1
    assert any("undeclared variable 'y'" in e.message for e in errors)


def test_reports_redeclaration_in_same_scope():
    source = """
    let x: int = 1;
    let x: int = 2;
    """
    _symbols, errors = _analyze(source)

    assert len(errors) >= 1
    assert any("Redeclaration of variable 'x'" in e.message for e in errors)


def test_allows_shadowing_in_nested_scope():
    source = """
    let x: int = 1;
    if (true) {
        let x: int = 2;
        print(x);
    }
    print(x);
    """
    _symbols, errors = _analyze(source)

    assert errors == []


def test_reports_type_mismatch_in_declaration_and_assignment():
    source = """
    let a: int = true;
    let b: int = 1;
    b = "hello";
    """
    _symbols, errors = _analyze(source)

    assert len(errors) >= 2
    assert any("Type mismatch in declaration of 'a'" in e.message for e in errors)
    assert any("Type mismatch in assignment to 'b'" in e.message for e in errors)


def test_reports_non_bool_condition():
    source = """
    let x: int = 1;
    while (x) {
        x = x + 1;
    }
    """
    _symbols, errors = _analyze(source)

    assert len(errors) >= 1
    assert any("While condition must be of type bool" in e.message for e in errors)


def test_valid_array_and_dictionary_indexing_has_no_semantic_errors():
    source = '''
    let arr: array = [1, 2, 3];
    let data: dict = {"a": 10, "b": 20};
    print(arr[1]);
    print(data["a"]);
    '''

    symbols, errors = _analyze(source)

    assert errors == []
    names = [s.name for s in symbols]
    assert "arr" in names
    assert "data" in names


def test_reports_array_literal_type_inconsistency():
    source = 'let arr: array = [1, "two", 3];'

    _symbols, errors = _analyze(source)

    assert len(errors) >= 1
    assert any("Array literal elements must all have the same type" in e.message for e in errors)
    first = next(e for e in errors if "Array literal elements must all have the same type" in e.message)
    assert first.line > 0
    assert first.column > 0


def test_reports_dictionary_key_type_inconsistency():
    source = 'let data: dict = {"a": 1, 2: 3};'

    _symbols, errors = _analyze(source)

    assert len(errors) >= 1
    assert any("Dictionary literal keys must all have the same type" in e.message for e in errors)
    first = next(e for e in errors if "Dictionary literal keys must all have the same type" in e.message)
    assert first.line > 0
    assert first.column > 0
