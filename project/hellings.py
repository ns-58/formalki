from project.cfg import cfg_to_weak_normal_form
import pyformlang
import networkx as nx


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
    result = {(v, u) for (nt, v, u) in r if nt == pyformlang.cfg.Terminal("S")}
    return result
