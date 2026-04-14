import project.hellings as hel
import graphs
from pyformlang.cfg import CFG


def test_hel_none_none():
    assert hel.hellings_based_cfpq(
        CFG.from_text("S -> S a | $"),
        graphs.point_graph,
    ) == {
        (
            1,
            1,
        )
    }
