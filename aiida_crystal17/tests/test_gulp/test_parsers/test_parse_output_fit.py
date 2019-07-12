import os

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.gulp.parsers.raw.parse_output_fit import parse_file


def test_parse_file_lj(data_regression):
    with open(os.path.join(TEST_FILES, 'gulp', 'fit_lj_fes', 'main.gout')) as handle:
        data, exit_code = parse_file(handle)
    data_regression.check(data)
    assert exit_code is None


def test_parse_file_reaxff(data_regression):
    with open(os.path.join(TEST_FILES, 'gulp', 'fit_reaxff_fes', 'main.gout')) as handle:
        data, exit_code = parse_file(handle)
    data_regression.check(data)
    assert exit_code is None
