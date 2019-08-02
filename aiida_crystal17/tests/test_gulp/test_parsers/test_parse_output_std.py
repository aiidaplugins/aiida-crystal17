import os

from aiida_crystal17 import __version__
from aiida_crystal17.common import recursive_round
from aiida_crystal17.gulp.parsers.raw.parse_output_std import parse_file
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_parse_failed():
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, 'gulp', 'failed', 'empty_error.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class')

    assert exit_code == 'ERROR_GULP_UNHANDLED'

    expected = {
        'parser_errors': ['Reached end of file before finding output section'],
        'parser_warnings': [],
        'parser_version': __version__,
        'gulp_version': '4.5.3',
        'errors': ['!! ERROR : input file is empty'],
        'warnings': [],
        'energy_units': 'eV',
        'parser_class': 'test_class'
    }

    assert data == expected


def test_parse_failed_optimize(data_regression):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, 'gulp', 'failed', 'opt_step_limit.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class')

    result = recursive_round(data, 6)
    result.pop('parser_version')
    data_regression.check(result)

    assert exit_code == 'ERROR_OPTIMISE_MAX_ATTEMPTS'


def test_parse_non_primitive_opt(data_regression):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, 'gulp', 'non_primitive_opt', 'main.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class')

    result = recursive_round(data, 6)
    result.pop('parser_version')
    data_regression.check(result)

    assert exit_code is None


def test_parse_surface_opt(data_regression):
    # type: (AiidaTestApp) -> None
    """ this is a surface calculation """
    path = os.path.join(TEST_FILES, 'gulp', 'surface_opt', 'main.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class')

    result = recursive_round(data, 6)
    result.pop('parser_version')
    data_regression.check(result)

    assert exit_code is None


def test_parse_polymer_opt(data_regression):
    # type: (AiidaTestApp) -> None
    """ this is a surface calculation """
    path = os.path.join(TEST_FILES, 'gulp', 's2_polymer_opt', 'main.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class')

    result = recursive_round(data, 6)
    result.pop('parser_version')
    data_regression.check(result)

    assert exit_code is None


def test_parse_single_lj_pyrite(data_regression):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, 'gulp', 'single_lj_pyrite', 'main.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class', single_point_only=True)

    result = recursive_round(data, 6)
    result.pop('parser_version')
    data_regression.check(result)

    assert exit_code is None


def test_parse_single_reaxff_pyrite(data_regression):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, 'gulp', 'single_reaxff_pyrite', 'main.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class', single_point_only=True)

    result = recursive_round(data, 6)
    result.pop('parser_version')
    data_regression.check(result)

    assert exit_code is None


def test_parse_optimize_reaxff_pyrite(data_regression):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, 'gulp', 'optimize_reaxff_pyrite_symm', 'main.gout')
    with open(path) as handle:
        data, exit_code = parse_file(handle, 'test_class')

    result = recursive_round(data, 6)
    result.pop('parser_version')
    data_regression.check(result)

    assert exit_code is None
