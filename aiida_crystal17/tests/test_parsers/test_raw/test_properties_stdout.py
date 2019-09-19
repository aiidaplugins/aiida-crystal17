from aiida_crystal17.common import recursive_round
from aiida_crystal17.parsers.raw.properties_stdout import read_properties_stdout
from aiida_crystal17.tests import read_resource_text


def test_read_props_stdout_doss(data_regression):

    content = read_resource_text('doss', 'mgo_sto3g_scf', 'main.out')
    data = read_properties_stdout(content)
    data_regression.check(recursive_round(data, 2))


def test_read_props_stdout_ech3(data_regression):

    content = read_resource_text('ech3', 'mgo_sto3g_scf', 'main.out')
    data = read_properties_stdout(content)
    data_regression.check(recursive_round(data, 2))
