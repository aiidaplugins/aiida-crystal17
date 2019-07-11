import os
from jsonextended import edict

from aiida_crystal17 import __version__
from aiida_crystal17.gulp.parsers.raw.parse_output import parse_output
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_parse_failed(db_test_app):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, "gulp", "failed", 'empty_error.gout')
    with open(path) as handle:
        parse_result = parse_output(handle, "test_class")

    assert parse_result.exit_code.status != 0

    expected = {
        'parser_errors': ["expected 'initial' data"],
        'parser_warnings': [],
        'parser_version': __version__,
        'errors': ['!! ERROR : input file is empty'],
        'warnings': [],
        'energy_units': 'eV',
        'parser_class': 'test_class'
    }

    assert parse_result.nodes.results.get_dict() == expected


def test_parse_optimize_reaxff_pyrite(db_test_app):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_FILES, "gulp", "optimize_reaxff_pyrite_symm", 'main.gout')
    with open(path) as handle:
        parse_result = parse_output(handle, "test_class", final=True)

    assert parse_result.exit_code.status == 0

    expected = {
        'errors': [], 'warnings': [],
        'parser_version': __version__,
        'parser_class': 'test_class',
        'parser_warnings': [], 'parser_errors': [],
        'energy_units': 'eV',
        'energy_initial': -42.24545667,
        'energy': -47.40858937,
        'optimised': True,
        'energy_contributions': {
            'Bond': -78.05702943, 'Coulomb': -2.97478507, 'Torsion': 0.20219012,
            'Lone-Pair': 1.21399494, 'Conjugation': 0.0, 'Hydrogen Bond': 0.0,
            'Valence Angle': 14.01837821, 'van der Waals': 6.11205713,
            'Coordination (over)': 12.42317601, 'Charge Equilibration': -0.34657127,
            'Coordination (under)': 0.0, 'Valence Angle Conjugation': 0.0,
            'Double-Bond Valence Angle Penalty': 0.0}}

    assert edict.diff(
        parse_result.nodes.results.get_dict(), expected, np_allclose=True) == {}
