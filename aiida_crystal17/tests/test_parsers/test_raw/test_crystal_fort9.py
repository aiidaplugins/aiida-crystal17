from aiida_crystal17.common import recursive_round
from aiida_crystal17.parsers.raw.crystal_fort9 import parse_fort9
from aiida_crystal17.tests import open_resource_binary


def test_parse_fort9(data_regression):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "fort.9") as handle:
        results = parse_fort9(handle)

    data_regression.check(recursive_round(results._asdict(), 7))
