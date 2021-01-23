from pyomompsparser import parse
import pyomo.kernel as pk


def test_parse():
    """ very rushed test"""
    # Utterly shit to have this in the test but it's late on a Saturday night, apologies to future me
    model = parse(
        "/Users/michaelradigan/pyomo-mps-parser/mps/enlight8.mps")
    pk.SolverFactory('cbc').solve(model)
    assert model.o() == 27
