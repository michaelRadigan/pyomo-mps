from pyomompsparser import parse
import pyomo.kernel as pk
import os
import pytest

fixture_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_files',
)

enlight8_file_name = 'enlight8.mps'


@pytest.mark.datafiles(os.path.join(fixture_dir, enlight8_file_name))
def test_parse_enlight8(datafiles):
    """ very rushed test"""
    dir_path = str(datafiles)  # convert from py.path object to a  path
    assert len(os.listdir(dir_path)) == 1
    file_path = os.path.join(dir_path, enlight8_file_name)
    assert os.path.isfile(file_path)
    model = parse(file_path)
    pk.SolverFactory('cbc').solve(model)
    assert model.o() == 27
