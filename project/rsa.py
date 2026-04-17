import pyformlang
from itertools import groupby
from pyformlang.regular_expression import Regex
from functools import reduce
from project.automata import regex_to_dfa


class NoStartRulesError(Exception):
    def __init__(self, message="Grammar has no production rules from the start symbol"):
        self.message = message
        super().__init__(self.message)


def production_to_reg(prods) -> Regex:
    return reduce(
        lambda reg, obj: reg.concatenate(Regex(obj.to_text())),
        prods.body,
        Regex("$"),
    )


def cfg_to_rsm(cfg: pyformlang.cfg.CFG) -> pyformlang.rsa.RecursiveAutomaton:
    prods = groupby(
        sorted(cfg.productions, key=lambda p: p.head.to_text()),
        key=lambda p: p.head.to_text(),
    )
    boxes = set()
    labels = set()
    for hd, prods in prods:
        init = production_to_reg(next(prods))
        assert isinstance(init, Regex)
        reg = reduce(lambda reg, p: reg.union(production_to_reg(p)), prods, init)
        nfa = reg.to_epsilon_nfa().minimize()
        box = pyformlang.rsa.Box(nfa, hd)
        boxes.add(box)
        labels.add(pyformlang.finite_automaton.finite_automaton.to_symbol(hd))
    return pyformlang.rsa.RecursiveAutomaton(labels, cfg.start_symbol, boxes)


def ebnf_to_rsm(ebnf: str) -> pyformlang.rsa.RecursiveAutomaton:
    return pyformlang.rsa.from_ebnf(ebnf)
