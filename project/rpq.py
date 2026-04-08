from __future__ import annotations
from scipy.sparse import find
from networkx import MultiDiGraph
import numpy as np
from project.automata import graph_to_nfa, regex_to_dfa
from project.adjMat import AdjacencyMatrixFA, intersect_automata


def tensor_based_rpq(
    regex: str, graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int]
) -> set[tuple[int, int]]:
    aut1 = AdjacencyMatrixFA(regex_to_dfa(regex))
    aut2 = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))
    aut = intersect_automata(aut1, aut2)
    tcT = aut.trans_closure().transpose()
    res = set()

    for start_ind in aut.start_states:
        acc = []
        if start_ind in aut.final_states:
            acc.append((start_ind, start_ind))
        if tcT.count_nonzero() > 0:
            start_vector = np.array(
                [(i == start_ind) for i in range(0, aut1.mat_size * aut2.mat_size)],
                dtype=bool,
            )
            pos_fins = find(tcT @ start_vector)[1]
            for fin_ind in aut.final_states:
                if fin_ind in pos_fins:
                    acc.append((start_ind, fin_ind))
        res = res.union(
            [
                (
                    aut2.trans_states[start % aut2.mat_size],
                    aut2.trans_states[fin % aut2.mat_size],
                )
                for (start, fin) in acc
            ]
        )

    return res
