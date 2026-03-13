"""Phase 5 tests for TAC generator."""

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tac_generator import TACGenerator


def _generate_tac(source: str):
    tokens, lex_errors = Lexer(source).tokenize()
    assert lex_errors == []

    program, parse_errors = Parser(tokens).parse()
    assert parse_errors == []

    return TACGenerator().generate(program)


def test_generates_tac_for_expression_precedence():
    tac = _generate_tac("let x: int = 1 + 2 * 3;")

    ops = [i.op for i in tac]
    assert "*" in ops
    assert "+" in ops
    assert "ASSIGN" in ops

    mul_idx = ops.index("*")
    plus_idx = ops.index("+")
    assign_idx = ops.index("ASSIGN")

    assert mul_idx < plus_idx < assign_idx
    assert tac[-1].result == "x"


def test_generates_tac_for_if_else_and_while_control_flow():
    source = """
    let x: int = 0;
    if (x < 1) {
        print(x);
    } else {
        print(1);
    }
    while (x < 2) {
        x = x + 1;
    }
    """
    tac = _generate_tac(source)

    ops = [i.op for i in tac]

    assert ops.count("IF_FALSE_GOTO") >= 2
    assert "GOTO" in ops
    assert ops.count("LABEL") >= 4
    assert "PRINT" in ops


def test_generates_tac_for_assignment_and_unary_ops():
    source = """
    let x: int = 1;
    x = -x;
    print(!false);
    """
    tac = _generate_tac(source)

    ops = [i.op for i in tac]

    assert "NEG" in ops
    assert "NOT" in ops
    assert ops.count("ASSIGN") >= 2
    assert "PRINT" in ops
