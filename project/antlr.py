from antlr4 import (
    ParserRuleContext,
    InputStream,
    CommonTokenStream,
    ParseTreeWalker,
    TerminalNode,
)
from antlr4.error.ErrorListener import ErrorListener
from project.QLangLexer import QLangLexer
from project.QLangParser import QLangParser
from project.QLangListener import QLangListener
from project.QLangVisitor import QLangVisitor


class LexerErrorListener(ErrorListener):
    def __init__(self) -> None:
        self.cntr = 0

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e) -> None:
        self.cntr += 1
        super().syntaxError(recognizer, offendingSymbol, line, column, msg, e)


# Второе поле показывает корректна ли строка (True, если корректна)
def program_to_tree(program: str) -> tuple[ParserRuleContext, bool]:
    input_stream = InputStream(program)
    lexer = QLangLexer(input_stream)
    lexer.removeErrorListener
    lex_err_listener = LexerErrorListener()
    lexer.addErrorListener(lex_err_listener)
    stream = CommonTokenStream(lexer)
    parser = QLangParser(stream)
    tree = parser.prog()
    return (tree, lex_err_listener.cntr == 0 and parser.getNumberOfSyntaxErrors() == 0)


class Nodes_Counter(QLangListener):
    def __init__(self):
        self.result = 0

    def enterEveryRule(self, ctx: ParserRuleContext):
        self.result += 1


def nodes_count(tree: ParserRuleContext) -> int:
    ctr = Nodes_Counter()
    walker = ParseTreeWalker()
    walker.walk(ctr, tree)
    return ctr.result


class Pprint(QLangVisitor):
    def __init__(self):
        self.result = []

    def getResultStr(self) -> str:
        return "".join(self.result)

    def visitProg(self, ctx: QLangParser.ProgContext):
        for ch in ctx.getChildren():
            self.visit(ch)
            self.result.append("\n")

    def visitTerminal(self, node: TerminalNode):
        self.result.append(node.getText())
        self.result.append(" ")


def tree_to_program(tree: ParserRuleContext) -> str:
    pprint = Pprint()
    pprint.visit(tree)
    return pprint.getResultStr()
