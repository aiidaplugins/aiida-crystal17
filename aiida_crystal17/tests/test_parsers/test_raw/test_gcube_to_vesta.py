import six

from aiida_crystal17.data.gcube import GaussianCube
from aiida_crystal17.parsers.raw.gaussian_cube import read_gaussian_cube
from aiida_crystal17.parsers.raw.gcube_to_vesta import (create_vesta_input, write_vesta_files)
from aiida_crystal17.tests import open_resource_binary, open_resource_text


def test_create_vesta_input(file_regression):

    with open_resource_text('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT') as handle:
        data = read_gaussian_cube(handle, return_density=False)
    content = create_vesta_input(data, 'input.cube', settings={'show_compass': False})
    file_regression.check(six.ensure_text(content), extension='.vesta')


def test_write_vesta_files(db_test_app):
    with open_resource_binary('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT') as handle:
        node = GaussianCube(handle)
    with db_test_app.sandbox_folder() as folder:
        write_vesta_files(node, folder.abspath, 'test')
        assert sorted(folder.get_content_list()) == sorted(['test.cube', 'test.vesta'])
