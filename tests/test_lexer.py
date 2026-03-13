"""Phase 2 tests for EduLang lexical analyzer."""

from compiler.lexer import Lexer


def _token_shapes(tokens):
    return [(t.token_type, t.lexeme) for t in tokens]


def test_tokenize_valid_declarations_and_print():
    source = "let x: int = 10; print(x);"
    tokens, errors = Lexer(source).tokenize()

    assert errors == []
    assert _token_shapes(tokens) == [
        ("KEYWORD", "let"),
        ("IDENTIFIER", "x"),
        ("SYMBOL", ":"),
        ("KEYWORD", "int"),
        ("OPERATOR", "="),
        ("INT_LITERAL", "10"),
        ("SYMBOL", ";"),
        ("KEYWORD", "print"),
        ("SYMBOL", "("),
        ("IDENTIFIER", "x"),
        ("SYMBOL", ")"),
        ("SYMBOL", ";"),
        ("EOF", ""),
    ]


def test_skips_comments_and_whitespace():
    source = "// line\nlet v: float = 2.5; /* block */"
    tokens, errors = Lexer(source).tokenize()

    assert errors == []
    assert _token_shapes(tokens) == [
        ("KEYWORD", "let"),
        ("IDENTIFIER", "v"),
        ("SYMBOL", ":"),
        ("KEYWORD", "float"),
        ("OPERATOR", "="),
        ("FLOAT_LITERAL", "2.5"),
        ("SYMBOL", ";"),
        ("EOF", ""),
    ]


def test_reports_unterminated_string():
    source = 'let s: string = "oops;'
    tokens, errors = Lexer(source).tokenize()

    assert len(errors) == 1
    assert "Unterminated string literal" in errors[0].message
    assert tokens[-1].token_type == "EOF"


def test_reports_invalid_character_and_malformed_number():
    source = "let x: int = 12.3.4; @"
    _tokens, errors = Lexer(source).tokenize()

    messages = [e.message for e in errors]
    assert any("Malformed number literal" in msg for msg in messages)
    assert any("Invalid character: @" in msg for msg in messages)
