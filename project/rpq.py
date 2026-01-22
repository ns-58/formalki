from __future__ import annotations
from scipy.sparse import csr_array, kron, find
from networkx import MultiDiGraph
from pyformlang.finite_automaton import NondeterministicFiniteAutomaton, Symbol
from typing import Dict, Set, Iterable
import numpy as np
from project.automata import graph_to_nfa, regex_to_dfa
from project.adjMat import AdjacencyMatrixFA, intersect_automata
def tensor_based_rpq(
    regex: str, graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int]
) -> set[tuple[int, int]]:
    aut1 = AdjacencyMatrixFA(regex_to_dfa(regex))
    aut2 = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))
    aut = intersect_automata(aut1,aut2)

    with open("out.txt", 'a') as f:
        print("aut1: ", list(map( lambda x : x.toarray(), aut1.b_mats.values())), file = f )
        print("aut2: ", list( map( lambda x : x.toarray(), aut2.b_mats.values())), file = f )
        print("aut: ", list( map( lambda x : x.toarray(), aut.b_mats.values())), file = f )
    tcT = aut.trans_closure().transpose()
    with open("out.txt", 'a') as f:
        print("TcT: ", tcT.toarray(), file = f )
    res = set()
    trans_states = lambda x, y : (aut2.trans_states[x % aut2.mat_size], aut2.trans_states[y % aut2.mat_size])
    for start_ind in aut.start_states:
        if start_ind in aut.final_states:
            res.add(( trans_states(start_ind, start_ind)))
        if tcT.count_nonzero() > 0:
            # не проще ли просто проекцию делать?
            start_vector = np.array([int(i == start_ind) for i in range (0, aut1.mat_size * aut2.mat_size)])
            pos_fins = find (tcT @ start_vector)[1]
            for fin_ind in aut.final_states:
                if fin_ind in pos_fins:
                    res.add(trans_states(start_ind, fin_ind))
    with open("out.txt", 'a') as f:
        print(res, file = f )
    return res
