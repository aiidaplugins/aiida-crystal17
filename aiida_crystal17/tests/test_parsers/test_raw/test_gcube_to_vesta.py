import six

from aiida_crystal17.parsers.raw.gaussian_cube import read_gaussian_cube
from aiida_crystal17.parsers.raw.gcube_to_vesta import create_vesta_input
from aiida_crystal17.tests import open_resource_text


def test_create_vesta_input(file_regression):

    with open_resource_text('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT') as handle:
        data = read_gaussian_cube(handle, return_density=False)
    content = create_vesta_input(data, 'input.cube')
    file_regression.check(six.ensure_text(content), extension='.vesta')
