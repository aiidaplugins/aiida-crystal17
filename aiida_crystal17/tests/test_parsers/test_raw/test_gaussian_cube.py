from aiida_crystal17.common import recursive_round
from aiida_crystal17.parsers.raw.gaussian_cube import read_gaussian_cube
from aiida_crystal17.tests import open_resource_text


def test_read_density_cube(data_regression):

    with open_resource_text("ech3", "mgo_sto3g_scf", "DENS_CUBE.DAT") as handle:
        data = read_gaussian_cube(handle, return_density=True)._asdict()
    data.pop("density")
    data_regression.check(recursive_round(data, 2))
