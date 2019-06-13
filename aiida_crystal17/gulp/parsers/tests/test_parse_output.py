import os
from jsonextended import edict

from aiida_crystal17 import __version__
from aiida_crystal17.gulp.parsers.parse_output import parse_output
from aiida_crystal17.tests import TEST_DIR
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_parse_failed(db_test_app):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_DIR, 'gulp_output_files', 'empty_error.gout')
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


def test_parse_opt_reaxff_pyrite(db_test_app):
    # type: (AiidaTestApp) -> None
    path = os.path.join(TEST_DIR, 'gulp_output_files', 'opt_reaxff_pyrite.gout')
    with open(path) as handle:
        parse_result = parse_output(handle, "test_class", final=True)

    assert parse_result.exit_code.status == 0

    expected = {
        'parser_errors': [],
        'parser_warnings': [],
        'parser_version': __version__,
        'errors': [],
        'warnings': [],
        'energy_contributions': {
            'Double-Bond Valence Angle Penalty': 0.0,
            'Charge Equilibration': -0.35733251,
            'Coulomb': -2.95800482,
            'Coordination (over)': 12.16296392,
            'Conjugation': 0.0,
            'Valence Angle': 13.80015008,
            'Hydrogen Bond': 0.0,
            'Valence Angle Conjugation': 0.0,
            'Coordination (under)': 0.0,
            'Torsion': 0.19158951,
            'Lone-Pair': 1.21399426,
            'van der Waals': 5.95617879,
            'Bond': -77.39551881
        },
        'optimised': True,
        'energy': -47.38597959,
        'energy_units': 'eV',
        'energy_initial': -42.20546311,
        'parser_class': 'test_class'
    }

    assert edict.diff(
        parse_result.nodes.results.get_dict(), expected, np_allclose=True) == {}
