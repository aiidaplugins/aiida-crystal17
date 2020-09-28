from aiida.plugins import DataFactory

from aiida_crystal17.common import recursive_round
from aiida_crystal17.data.gcube import GaussianCube
from aiida_crystal17.tests import open_resource_binary, resource_context


def test_entry_point(db_test_app):
    """test the plugin entry point works"""
    DataFactory("crystal17.gcube")


def test_read_filepath(db_test_app, data_regression):
    with resource_context("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as path:
        node = GaussianCube(str(path))
    data_regression.check(recursive_round(node.attributes, 5))


def test_read_fileobj(db_test_app, data_regression):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        node = GaussianCube(handle)
    data_regression.check(recursive_round(node.attributes, 5))


def test_open_gcube(db_test_app):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        node = GaussianCube(handle)
    with node.open_cube_file() as handle:
        line = handle.readline().strip()
    assert line == "Charge density - 3D GRID - GAUSSIAN CUBE FORMAT MgO Bulk"


def test_get_cube_data(db_test_app):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        node = GaussianCube(handle)
    data = node.get_cube_data()
    assert data.atoms_atomic_number == [12, 8]


def test_get_ase(db_test_app):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        node = GaussianCube(handle)
    atoms = node.get_ase()
    assert atoms.get_chemical_symbols() == ["Mg", "O"]


def test_compute_integration_cell(db_test_app):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        node = GaussianCube(handle)
    assert round(node.compute_integration_cell(), 1) == 18.6


def test_compute_integration_sphere(db_test_app):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        node = GaussianCube(handle)
    assert (
        round(
            node.compute_integration_sphere((0, 0, 0), 10, (False, False, False))[0], 1
        )
        == 18.6
    )
    assert (
        round(
            node.compute_integration_sphere((0, 0, 0), 1, (False, False, False))[0], 1
        )
        == 2.0
    )
    assert (
        round(node.compute_integration_sphere((0, 0, 0), 1, (True, True, True))[0], 1)
        == 17.2
    )


def test_compute_integration_atom(db_test_app):
    with open_resource_binary("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        node = GaussianCube(handle)
    assert [round(v, 1) for v in node.compute_integration_atom((0, 1), 2)] == [
        18.8,
        3.8,
    ]
