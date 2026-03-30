"""Phase 3 tests for EduLang syntax analyzer."""

from compiler.lexer import Lexer
from compiler.parser import (
    ArrayLiteralExpr,
    AssignmentStmt,
    BinaryExpr,
    DeclarationStmt,
    DictLiteralExpr,
    IndexExpr,
    IfStmt,
    Parser,
    PrintStmt,
    Program,
    WhileStmt,
)


def _parse(source: str):
    tokens, lex_errors = Lexer(source).tokenize()
    assert lex_errors == []
    return Parser(tokens).parse()


def test_parse_valid_program_builds_ast():
    source = """
    let x: int = 1;
    while (x < 3) {
        if (x == 2) {
            print(x);
        } else {
            print(0);
        }
        x = x + 1;
    }
    """

    program, errors = _parse(source)

    assert errors == []
    assert isinstance(program, Program)
    assert len(program.statements) == 2
    assert isinstance(program.statements[0], DeclarationStmt)
    assert isinstance(program.statements[1], WhileStmt)

    while_stmt = program.statements[1]
    assert isinstance(while_stmt.body.statements[0], IfStmt)
    assert isinstance(while_stmt.body.statements[1], AssignmentStmt)


def test_expression_precedence_in_ast():
    source = "let x: int = 1 + 2 * 3;"
    program, errors = _parse(source)

    assert errors == []
    decl = program.statements[0]
    assert isinstance(decl, DeclarationStmt)
    assert isinstance(decl.initializer, BinaryExpr)
    assert decl.initializer.operator == "+"
    assert isinstance(decl.initializer.right, BinaryExpr)
    assert decl.initializer.right.operator == "*"


def test_reports_syntax_error_and_recovers_to_next_statement():
    source = "let x: int = 1 print(x);"
    tokens, lex_errors = Lexer(source).tokenize()
    assert lex_errors == []

    program, errors = Parser(tokens).parse()

    assert len(errors) >= 1
    assert any("Expected ';' after declaration" in err.message for err in errors)
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], PrintStmt)


def test_reports_missing_if_parenthesis():
    source = "if (true { print(1); }"
    tokens, lex_errors = Lexer(source).tokenize()
    assert lex_errors == []

    _program, errors = Parser(tokens).parse()

    assert len(errors) >= 1
    assert any("Expected ')' after if condition" in err.message for err in errors)


def test_parse_array_and_dictionary_index_expressions():
    source = '''
    let arr: array = [1, 2, 3];
    let data: dict = {"a": 10, "b": 20};
    print(arr[1]);
    print(data["a"]);
    '''

    program, errors = _parse(source)

    assert errors == []
    arr_decl = program.statements[0]
    data_decl = program.statements[1]
    first_print = program.statements[2]
    second_print = program.statements[3]

    assert isinstance(arr_decl, DeclarationStmt)
    assert isinstance(arr_decl.initializer, ArrayLiteralExpr)
    assert isinstance(data_decl, DeclarationStmt)
    assert isinstance(data_decl.initializer, DictLiteralExpr)
    assert isinstance(first_print, PrintStmt)
    assert isinstance(first_print.expression, IndexExpr)
    assert isinstance(second_print, PrintStmt)
    assert isinstance(second_print.expression, IndexExpr)


def test_missing_dict_colon_reports_error_without_hanging():
    source = 'let data: dict = {"a" 10, "b": 20};\nprint(data["a"]);'
    tokens, lex_errors = Lexer(source).tokenize()
    assert lex_errors == []

    program, errors = Parser(tokens).parse()

    assert len(errors) >= 1
    assert any("Expected ':' between dictionary key and value" in err.message for err in errors)
    # Parser should recover and continue instead of looping forever.
    assert len(program.statements) >= 1
