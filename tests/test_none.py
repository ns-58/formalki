import project.hellings as hel
import graphs
from pyformlang.cfg import CFG
import pytest

def test_hel_none_none(self):
        assert hel.hellings_based_cfpq(graphs.point_graph, CFG.from_text("S -> a")) == (1,1)
