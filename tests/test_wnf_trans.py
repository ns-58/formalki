import pyformlang.cfg as cf
from project import cfg


class TestWNFTrans:
    def test_noepsilon_cfg(self):
        gr = cf.CFG.from_text("""
        S -> a b
        S -> a S b
        """)
        gr_wnf = cfg.cfg_to_weak_normal_form(gr)
        assert gr_wnf.is_normal_form()

    def test_epsilon_cfg(self):
        gr = cf.CFG.from_text("""
        S -> a b
        S -> C
        C -> epsilon
        S -> a S b
        """)
        gr_wnf = cfg.cfg_to_weak_normal_form(gr)
        assert gr_wnf.generate_epsilon()
        assert cfg.is_weak_normal_form(gr_wnf.productions)
