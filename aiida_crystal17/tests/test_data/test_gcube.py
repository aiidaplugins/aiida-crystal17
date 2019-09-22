import six

from aiida.plugins import DataFactory

from aiida_crystal17.common import recursive_round
from aiida_crystal17.data.gcube import GaussianCube
from aiida_crystal17.tests import resource_context, open_resource_binary


def test_read_filepath(db_test_app, data_regression):
    with resource_context('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT') as path:
        node = GaussianCube(str(path))
    data_regression.check(recursive_round(node.attributes, 5))


def test_read_fileobj(db_test_app, data_regression):
    with open_resource_binary('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT') as handle:
        node = GaussianCube(handle)
    data_regression.check(recursive_round(node.attributes, 5))


def test_open_gcube(db_test_app):
    with open_resource_binary('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT') as handle:
        node = GaussianCube(handle)
    with node.open_gcube() as handle:
        line = six.ensure_str(handle.readline().strip())
    assert line == 'Charge density - 3D GRID - GAUSSIAN CUBE FORMAT MgO Bulk'


def test_entry_point(db_test_app):
    """test the plugin entry point works"""
    DataFactory('crystal17.gcube')
