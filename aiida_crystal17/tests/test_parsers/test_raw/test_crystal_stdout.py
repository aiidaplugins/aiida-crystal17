import os
import pytest

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.common import recursive_round
from aiida_crystal17.parsers.raw.crystal_stdout import read_crystal_stdout


@pytest.mark.parametrize('filename',
                         ('cry14_scf_and_opt.out', 'cry14_scf_only.out',
                          'cry14_scf_and_opt_slab.out', 'cry17_spin_opt.out'))
def test_crystal_stdout_files(filename, data_regression):
    path = os.path.join(TEST_FILES, "crystal", "stdout_parser", filename)
    with open(path) as handle:
        lines = handle.read().splitlines()
    output = read_crystal_stdout(lines)
    output = recursive_round(output, 12)
    data_regression.check(output)
