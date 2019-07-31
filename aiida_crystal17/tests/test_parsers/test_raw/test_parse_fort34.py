import os
import numpy as np
import pytest

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.parsers.raw.parse_fort34 import (parse_fort34, gui_file_write, get_centering_code,
                                                      get_crystal_type_code, structure_to_symmetry)


@pytest.mark.parametrize(
    'gui_filename,num_symops,space_group',
    (('cubic-rocksalt.crystal.gui', 48, 225), ('cubic-zincblende.crystal.gui', 24, 216),
     ('greigite.crystal.gui', 48, 227), ('mackinawite.crystal.gui', 16, 129), ('marcasite.crystal.gui', 8, 58),
     ('pyrite.crystal.gui', 24, 205), ('pyrrhotite-4c-monoclinic.crystal.gui', 4, 15),
     ('troilite-hex-p63mc.crystal.gui', 12, 186), ('troilite-hex-p63mmc.crystal.gui', 24, 194),
     ('troilite-hexagonal.crystal.gui', 12, 190), ('troilite-mnp.crystal.gui', 8, 62)))
def test_gui_file_read(gui_filename, num_symops, space_group):
    path = os.path.join(TEST_FILES, 'gui', 'out', gui_filename)
    with open(path) as handle:
        lines = handle.read().splitlines()
    structdata, symmdata = parse_fort34(lines)
    assert len(symmdata['operations']) == num_symops
    assert symmdata['space_group'] == space_group


@pytest.mark.parametrize(
    'hall_number,centering_code,crystal_code',
    [
        (90, 4, 2),  # pyrrhotite-4c 15, 'C2/c'
        (501, 1, 6),  # pyrite 205, 'Pa3'
        (275, 1, 3),  # marcasite 58, 'Pnnm'
        (484, 1, 5),  # troilite 190 'P-62c'
        (409, 1, 4),  # mackinawite 129, 'P4/nmm'
        (526, 5, 6)  # greigite 227, 'Fd3m'
    ])
def test_symmetry_codes(hall_number, centering_code, crystal_code):
    assert get_crystal_type_code(hall_number=hall_number) == crystal_code
    assert get_centering_code(hall_number) == centering_code


@pytest.mark.parametrize(
    'gui_filename,num_symops,space_group',
    (('cubic-rocksalt.crystal.gui', 48, 225), ('cubic-zincblende.crystal.gui', 24, 216),
     ('greigite.crystal.gui', 48, 227), ('mackinawite.crystal.gui', 16, 129), ('marcasite.crystal.gui', 8, 58),
     ('pyrite.crystal.gui', 24, 205), ('pyrrhotite-4c-monoclinic.crystal.gui', 4, 15),
     ('troilite-hex-p63mc.crystal.gui', 12, 186), ('troilite-hex-p63mmc.crystal.gui', 24, 194),
     ('troilite-hexagonal.crystal.gui', 12, 190), ('troilite-mnp.crystal.gui', 8, 62)))
def test_structure_to_symmetry(db_test_app, gui_filename, num_symops, space_group):
    """ we test that we can go round trip,
    reading a gui file and comparing the parsed symmetry to the computed one
    """
    path = os.path.join(TEST_FILES, 'gui', 'out', gui_filename)
    with open(path) as handle:
        lines = handle.read().splitlines()
    structdata, symmdata = parse_fort34(lines)

    symmdata2 = structure_to_symmetry(structdata)
    assert len(symmdata['operations']) == len(symmdata2['operations'])
    assert symmdata['space_group'] == symmdata2['space_group']
    assert symmdata['crystal_type_code'] == symmdata2['crystal_type_code']
    assert symmdata['centring_code'] == symmdata2['centring_code']


@pytest.mark.parametrize(
    'gui_filename,num_symops,space_group',
    (('cubic-rocksalt.crystal.gui', 48, 225), ('cubic-zincblende.crystal.gui', 24, 216),
     ('greigite.crystal.gui', 48, 227), ('mackinawite.crystal.gui', 16, 129), ('marcasite.crystal.gui', 8, 58),
     ('pyrite.crystal.gui', 24, 205), ('pyrrhotite-4c-monoclinic.crystal.gui', 4, 15),
     ('troilite-hex-p63mc.crystal.gui', 12, 186), ('troilite-hex-p63mmc.crystal.gui', 24, 194),
     ('troilite-hexagonal.crystal.gui', 12, 190), ('troilite-mnp.crystal.gui', 8, 62)))
def test_structure_to_symmetry_operations(db_test_app, gui_filename, num_symops, space_group):
    """ we test that we can go round trip,
    reading a gui file and comparing the parsed symmetry to the computed one
    """
    path = os.path.join(TEST_FILES, 'gui', 'out', gui_filename)
    with open(path) as handle:
        lines = handle.read().splitlines()
    structdata, symmdata = parse_fort34(lines)

    symmdata2 = structure_to_symmetry(structdata, as_cartesian=True)
    assert len(symmdata['operations']) == len(symmdata2['operations'])
    ops1 = np.sort(symmdata['operations'], axis=0)
    ops2 = np.sort(symmdata2['operations'], axis=0)
    assert np.allclose(ops1, ops2)


def test_gui_file_write():
    structure_data = {
        'lattice': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        'ccoords': [[0, 0, 0]],
        'atomic_numbers': [1],
        'pbc': [True, True, True]
    }
    symmetry_data = {
        'operations': [[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]],
        'basis': 'cartesian',
        'space_group': 4,
        'crystal_type_code': 5,
        'centring_code': 6
    }

    outstr = gui_file_write(structure_data, symmetry_data)

    print(outstr)

    expected = [
        '3 6 5', '  1.000000000E+00   0.000000000E+00   0.000000000E+00',
        '  0.000000000E+00   1.000000000E+00   0.000000000E+00',
        '  0.000000000E+00   0.000000000E+00   1.000000000E+00', '1',
        '  1.000000000E+00   0.000000000E+00   0.000000000E+00',
        '  0.000000000E+00   1.000000000E+00   0.000000000E+00',
        '  0.000000000E+00   0.000000000E+00   1.000000000E+00',
        '  0.000000000E+00   0.000000000E+00   0.000000000E+00', '1',
        '  1   0.000000000E+00   0.000000000E+00   0.000000000E+00', '4 1', ''
    ]
    assert outstr == expected
