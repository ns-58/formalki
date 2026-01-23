from __future__ import annotations
from scipy.sparse import find, csr_array
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
                [int(i == start_ind) for i in range(0, aut1.mat_size * aut2.mat_size)]
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


def ms_bfs_based_rpq(
    regex: str, graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int]
) -> set[tuple[int, int]]:
    aut1 = AdjacencyMatrixFA(regex_to_dfa(regex))
    aut2 = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))
    both = [
        (v.transpose(), aut1.b_mats[k])
        for (k, v) in aut2.b_mats.items()
        if k in aut1.b_mats.keys()
    ]
    res = set()
    for s2 in aut2.start_states:
        data, column_ind = [], []
        for s1 in aut1.start_states:
            data.append(1)
            column_ind.append(s1)
        front = csr_array(
            (data, ([s2 for _ in data], column_ind)),
            shape=(aut2.mat_size, aut1.mat_size),
        )
        acc = front.copy()
        while True:
            prev_nonzero_count = acc.count_nonzero()
            todo = []
            for gT, q in both:
                todo.append(gT @ front @ q)
            if len(todo) > 0:
                front = todo[0]
                for m in todo[1:]:
                    front = front.maximum(m)
                acc = acc.maximum(front)
            new_nonzero_count = acc.count_nonzero()
            if prev_nonzero_count == new_nonzero_count:
                nonzero = find(acc)
                for i in range(0, len(nonzero[0])):
                    pos_fin = nonzero[0][i]
                    if pos_fin in aut2.final_states:
                        if nonzero[1][i] in aut1.final_states:
                            res.add((aut2.trans_states[s2], aut2.trans_states[pos_fin]))
                break
    return res
