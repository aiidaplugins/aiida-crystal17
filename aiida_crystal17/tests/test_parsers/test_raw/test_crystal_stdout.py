import os
import pytest

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.common import recursive_round
from aiida_crystal17.parsers.raw.crystal_stdout import read_crystal_stdout


@pytest.mark.parametrize('name,filepath', (
    ('cry14_opt', ('crystal', 'stdout_parser', 'cry14_scf_and_opt.out')),
    ('cry14_scf', ('crystal', 'stdout_parser', 'cry14_scf_only.out')),
    ('cry14_opt_slab',
     ('crystal', 'stdout_parser', 'cry14_scf_and_opt_slab.out')),
    ('cry17_opt_spin', ('crystal', 'stdout_parser', 'cry17_spin_opt.out')),
    ('mgo_scf', ('crystal', 'mgo_sto3g_scf', 'main.out')),
    ('mgo_opt', ('crystal', 'mgo_sto3g_opt', 'main.out')),
    ('nio_scf', ('crystal', 'nio_sto3g_afm_scf', 'main.out')),
    ('nio_opt', ('crystal', 'nio_sto3g_afm_opt', 'main.out')),
    ('nio_opt_walltime',
     ('crystal', 'nio_sto3g_afm_opt_walltime', 'main.out')),
    ('nio_scf_maxcyc', ('crystal', 'nio_sto3g_afm_scf_maxcyc', 'main.out')),
    ('cry17_incomplete_scf',
     ('crystal', 'stdout_parser', 'cry17_incomplete_scf.out')),
    ('empty', ('crystal', 'stdout_parser', 'empty.out')),
    ('s2_molecule_opt', ('crystal', 's2_molecule_opt', 'main.out')),
    ('slab_testgeom', ('crystal', 'slab_testgeom', 'main.out'))
))
def test_crystal_stdout_files(name, filepath, data_regression):

    path = os.path.join(TEST_FILES, *filepath)
    with open(path) as handle:
        content = handle.read()
    output = read_crystal_stdout(content)
    output = recursive_round(output, 12)
    data_regression.check(output)
