from project import antlr


def test_lex_error1():
    _, is_ok = antlr.program_to_tree("Let x = 58")
    assert not is_ok


def test_lex_error2():
    _, is_ok = antlr.program_to_tree("let X = 58")
    assert not is_ok


def test_lex_error3():
    _, is_ok = antlr.program_to_tree("let x % 58")
    assert not is_ok
