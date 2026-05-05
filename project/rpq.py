from __future__ import annotations
from scipy.sparse import find, csc_array, hstack
from networkx import MultiDiGraph
from project.automata import graph_to_nfa, regex_to_dfa
from project.adjMat import AdjacencyMatrixFA, intersect_automata
from numpy import array


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
            start_vector = array(
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


def ms_bfs_based_rpq(
    regex: str, graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int]
) -> set[tuple[int, int]]:
    aut1 = AdjacencyMatrixFA(regex_to_dfa(regex))
    aut2 = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))
    both = [
        (v.transpose(), aut1.b_mats[k])
        for (k, v) in aut2.b_mats.items()
        if k in aut1.b_mats.keys() and v.count_nonzero() != 0
    ]
    res = set()
    fronts: list[csc_array] = []
    aut2_start_states = list(aut2.start_states)

    for s2 in aut2_start_states:
        data, column_ind = [], []
        for s1 in aut1.start_states:
            data.append(True)
            column_ind.append(s1)
        fronts.append(
            csc_array(
                (data, ([s2 for _ in data], column_ind)),
                shape=(aut2.mat_size, aut1.mat_size),
                dtype=bool,
            )
        )
    for f in fronts:
        assert f.shape == (aut2.mat_size, aut1.mat_size)
    fr = hstack(fronts)

    acc = fr.copy()
    fronts_count = len(fronts)

    while fr.count_nonzero() != 0:
        todo = []
        for gT, q in both:
            tmp = gT @ fr

            for i in range(0, fronts_count):
                tmp[:, i * aut1.mat_size : (i + 1) * aut1.mat_size] = (
                    tmp[:, i * aut1.mat_size : (i + 1) * aut1.mat_size] @ q
                )
            todo.append(tmp)
        if len(todo) > 0:
            fr = todo[0]
            for m in todo[1:]:
                fr = fr.maximum(m)

        fr = fr.minimum(fr - acc)
        acc = acc.maximum(fr)
    nonzero = find(acc)

    for pos_fin in zip(nonzero[0], nonzero[1]):
        if (
            pos_fin[0] in aut2.final_states
            and pos_fin[1] % aut1.mat_size in aut1.final_states
        ):
            res.add(
                (
                    aut2.trans_states[aut2_start_states[pos_fin[1] // aut1.mat_size]],
                    aut2.trans_states[pos_fin[0]],
                )
            )
    return res
