import pyformlang.cfg as cf
from typing import Iterable


def is_weak_normal_form(cfg_productions: Iterable[cf.production.Production]) -> bool:
    def is_prod_wnf(p: cf.production.Production) -> bool:
        body = p.body
        if len(body) == 2:
            return isinstance(body[0], cf.Variable) and isinstance(body[1], cf.Variable)
        if len(body) == 1:
            return isinstance(body[0], cf.Terminal)
        return not body

    return all(is_prod_wnf(p) for p in cfg_productions)


def cfg_to_weak_normal_form(cfg: cf.CFG) -> cf.CFG:
    if is_weak_normal_form(cfg.productions):
        return cfg
    unit_pairs = cfg.get_unit_pairs()
    generating = cfg.get_generating_symbols()
    reachables = cfg.get_reachable_symbols()
    if (
        len(unit_pairs) != len(cfg.variables)
        or len(generating) != len(cfg.variables) + len(cfg.terminals)
        or len(reachables) != len(cfg.variables) + len(cfg.terminals)
    ):
        if len(cfg.productions) == 0:
            return cfg
        new_cfg = (
            cfg.remove_useless_symbols()
            .eliminate_unit_productions()
            .remove_useless_symbols()
        )

        cfg = cfg_to_weak_normal_form(new_cfg)
        return cfg
    new_productions = cfg._get_productions_with_only_single_terminals()
    new_productions = cfg._decompose_productions(new_productions)
    cfg = cf.CFG(start_symbol=cfg.start_symbol, productions=set(new_productions))
    return cfg
