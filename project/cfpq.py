from project.cfg import cfg_to_weak_normal_form
import pyformlang
import networkx as nx
from scipy.sparse import find, csr_array, block_diag, eye_array
from project.adjMat import AdjacencyMatrixFA, intersect_automata
from project.automata import graph_to_nfa
from pyformlang.finite_automaton import NondeterministicFiniteAutomaton, Symbol




def hellings_based_cfpq(
    cfg: pyformlang.cfg.CFG,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:
    cfg = cfg_to_weak_normal_form(cfg)
    r = []
    for p in cfg.productions:
        if len(p.body) == 0:  # epsilon
            r += [(p.head, v, v) for v in graph.nodes]
        elif len(p.body) == 1 and isinstance(p.body[0], pyformlang.cfg.Terminal):
            exp_label = p.body[0].to_text()
            r += [
                (p.head, v, u)
                for (v, u, data) in graph.edges.data()
                if str(data["label"]) == exp_label
            ]
    m = r.copy()
    while m:
        (nt, v, u) = m.pop(0)
        for nt2, w in [(nt2, w) for (nt2, w, v2) in r if v == v2]:
            for nt3 in [
                p.head
                for p in cfg.productions
                if len(p.body) == 2 and p.body[0] == nt2 and p.body[1] == nt
            ]:
                if r.count((nt3, w, u)) == 0:
                    r.append((nt3, w, u))
                    m.append(((nt3, w, u)))
        for nt2, w in [(nt2, w) for (nt2, u2, w) in r if u == u2]:
            for nt3 in [
                p.head
                for p in cfg.productions
                if len(p.body) == 2 and p.body[0] == nt and p.body[1] == nt2
            ]:
                if r.count((nt3, v, w)) == 0:
                    r.append((nt3, v, w))
                    m.append(((nt3, v, w)))
    result = {
        (v, u)
        for (nt, v, u) in r
        if nt == pyformlang.cfg.Terminal("S") and v in start_nodes and u in final_nodes
    }
    return result


def matrix_based_cfpq(
    cfg: pyformlang.cfg.CFG,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:
    cfg = cfg_to_weak_normal_form(cfg)
    aut2 = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))
    nodes_count = len(graph.nodes)
    init_trans = {}
    len2_prods = []

    for p in cfg.productions:
        if len(p.body) == 0:  # epsilon
            dd, vv = [], []
            for v in range(0, aut2.mat_size):
                dd.append(1)
                vv.append(v)
            uu = vv.copy()
            add_trans(dd, vv, uu, init_trans, p.head)
        elif len(p.body) == 1 and isinstance(p.body[0], pyformlang.cfg.Terminal):
            label = p.body[0].to_text()
            if label in aut2.b_mats:
                vv, uu, dd = find(aut2.b_mats[label])
                add_trans(list(dd), list(vv), list(uu), init_trans, p.head)
        else:
            len2_prods.append(p)
    b_mats = {
        nt: csr_array((dd, (vv, uu)), shape=(nodes_count, nodes_count))
        for (nt, (dd, vv, uu)) in init_trans.items()
    }
    zero = csr_array(([], ([], [])), shape=(nodes_count, nodes_count))
    while True:
        is_changed = False
        for p in len2_prods:
            m1, m2, m3 = [
                get_with_def(b_mats, nt, zero) for nt in (p.head, p.body[0], p.body[1])
            ]
            tmp = m1.maximum(m2 @ m3)
            if tmp.count_nonzero() != m1.count_nonzero():
                is_changed = True
            b_mats[p.head] = tmp
        if not is_changed:
            break
    vv, uu, _ = find(get_with_def(b_mats, pyformlang.cfg.Variable("S"), zero))
    res = {
        (aut2.trans_states[v], aut2.trans_states[u])
        for (v, u) in zip(vv, uu)
        if v in aut2.start_states and u in aut2.final_states
    }
    return res


def add_trans(dd, vv, uu, acc, k):
    if k not in acc:
        acc[k] = (dd, vv, uu)
    else:
        prev = acc[k]
        acc[k] = (prev[0] + dd, prev[1] + vv, prev[2] + uu)


def get_with_def(dict, k, default):
    if k in dict:
        return dict[k]
    else:
        return default


def tensor_based_cfpq(
    rsm: pyformlang.rsa.RecursiveAutomaton,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:
    start_nodes = start_nodes if start_nodes else set(graph.nodes)
    final_nodes = final_nodes if final_nodes else set(graph.nodes)
    aut2 = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))
    coord = 0
    block_max_coords, auts = [], []
    alph = []
    starts, finals = [], []
    for sym, b in rsm.boxes.items():
        aut = AdjacencyMatrixFA(b.dfa)
        if aut.accepts([]):  # epsilon
            aut2.b_mats[sym] = eye_array(aut2.mat_size, dtype=bool)
        auts.append(aut)
        alph += aut.b_mats.keys()
        starts += [s + coord for s in aut.start_states]
        finals += [s + coord for s in aut.final_states]
        coord += aut.mat_size
        block_max_coords.append((coord, sym))
    starts, finals, alph = set(starts), set(finals), set(alph)
    aut1 = AdjacencyMatrixFA(NondeterministicFiniteAutomaton())
    aut1.Set(
        {
            sym: block_diag(
                [
                    csr_array(
                        ([], ([], [])), shape=(a.mat_size, a.mat_size), dtype=bool
                    )
                    if sym not in a.b_mats
                    else a.b_mats[sym]
                    for a in auts
                ],
                format="csr",
            )
            for sym in alph
        },
        starts,
        finals,
    )

    finish = False
    while not finish:
        aut = intersect_automata(aut1, aut2)
        finish = True
        tc = aut.trans_closure()
        nonzero = find(tc)
        for s, f in zip(nonzero[0], nonzero[1]):
            if (
                s // aut2.mat_size in aut1.start_states
                and f // aut2.mat_size in aut1.final_states
            ):
                syms = tuple(
                    map(
                        lambda st: next(
                            (
                                sy
                                for (max_coord, sy) in block_max_coords
                                if max_coord * aut2.mat_size > st
                            ),
                            None,
                        ),
                        (s, f),
                    )
                )

                if syms[0] == syms[1]:
                    v = csr_array(
                        ([True], ([s % aut2.mat_size], [f % aut2.mat_size])),
                        shape=(aut2.mat_size, aut2.mat_size),
                        dtype=bool,
                    )
                    if syms[0] not in aut2.b_mats:
                        finish = False
                        aut2.b_mats[syms[0]] = v
                    else:
                        nnz_count = aut2.b_mats[syms[0]].count_nonzero()
                        aut2.b_mats[syms[0]] = aut2.b_mats[syms[0]] + v
                        if nnz_count != aut2.b_mats[syms[0]].count_nonzero():
                            finish = False

    if Symbol(rsm.initial_label) not in aut2.b_mats:
        return set()
    nonzero = find(aut2.b_mats[Symbol(rsm.initial_label)])
    return {
        (aut2.trans_states[s], aut2.trans_states[f])
        for (s, f) in zip(nonzero[0], nonzero[1])
        if s in aut2.start_states and f in aut2.final_states
    }
