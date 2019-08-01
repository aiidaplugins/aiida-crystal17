import os
import pytest

from aiida_crystal17.parsers.raw import parse_bases
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.common import recursive_round


@pytest.mark.parametrize('filename', ('3-21g', '3-21g-star', 'tzvp', 'free', 'barthe', 'free_ecp', 'haywlc'))
def test_single_bases(filename, data_regression):
    path = os.path.join(TEST_FILES, 'basis_sets', 'manual_examples', filename + '.basis')
    with open(path) as handle:
        content = handle.read()
    output = parse_bases.parse_bsets_stdin(content, isolated=True)
    output = recursive_round(output, 12)
    data_regression.check(output)


@pytest.mark.parametrize('name,filepath', (
    ('mgo_sto3g', ('crystal', 'mgo_sto3g_scf', 'INPUT')),
    ('nio_sto3g', ('crystal', 'nio_sto3g_afm_scf', 'INPUT')),
))
def test_full_files(name, filepath, data_regression):
    path = os.path.join(TEST_FILES, *filepath)
    with open(path) as handle:
        content = handle.read()
    output = parse_bases.parse_bsets_stdin(content, isolated=False)
    output = recursive_round(output, 12)
    data_regression.check(output)
