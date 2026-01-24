from project.cfg import cfg_to_weak_normal_form
import pyformlang
import networkx as nx
from scipy.sparse import find, csr_array
from project.adjMat import AdjacencyMatrixFA
from project.automata import graph_to_nfa


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
