# -*- coding: utf-8 -*-
import os  # noqa: F401
from jsonextended import edict
from aiida_crystal17 import __version__
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401
from aiida_crystal17.tests import TEST_FILES  # noqa: F401
from aiida_crystal17.gulp.parsers.raw.write_input import (  # noqa: F401
    InputCreationSingle, InputCreationOpt)


def write_input_file(icreate, file_like, structure, potential,
                     parameters=None, symmetry=None):
    icreate.create_content(structure, potential.get_input_lines(), parameters, symmetry)
    icreate.write_content(file_like)
    return icreate.get_content_hash()


def test_run_single_lj(db_test_app, get_structure, pyrite_potential_lj):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    code = db_test_app.get_or_create_code('gulp.single')
    builder = code.get_builder()
    builder._update({"metadata": {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 30
        }
    }})
    builder.structure = get_structure("pyrite")
    builder.potential = pyrite_potential_lj

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ["results"])

    expected = {'energy': -0.32809466,
                'energy_units': 'eV',
                'errors': [],
                'parser_class': 'GulpSingleParser',
                'parser_errors': [],
                'parser_version': __version__,
                'parser_warnings': [],
                'warnings': []}
    assert edict.diff(
        calc_node.outputs.results.get_dict(), expected, np_allclose=True) == {}


def test_run_single_reaxff(db_test_app, get_structure, pyrite_potential_reaxff_lowtol):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    code = db_test_app.get_or_create_code('gulp.single')
    builder = code.get_builder()
    builder._update({"metadata": {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 30
        }
    }})
    builder.structure = get_structure("pyrite")
    builder.potential = pyrite_potential_reaxff_lowtol

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ["results"])

    expected = {
        'errors': [], 'warnings': [], 'parser_errors': [],
        'parser_version': __version__,
        'parser_class': 'GulpSingleParser', 'parser_warnings': [],
        'energy_units': 'eV', 'energy': -44.60033156,  # this is ≈ lammps result
        'energy_contributions': {
            'Bond': -78.23660866, 'Coulomb': -3.34422152, 'Torsion': 0.0,
            'Lone-Pair': 1.21399347, 'Conjugation': 0.0, 'Hydrogen Bond': 0.0,
            'Valence Angle': 16.66895737, 'van der Waals': 6.41369507,
            'Coordination (over)': 12.7899399,
            'Charge Equilibration': -0.10608718, 'Coordination (under)': 0.0,
            'Valence Angle Conjugation': 0.0,
            'Double-Bond Valence Angle Penalty': 0.0}}
    assert edict.diff(
        calc_node.outputs.results.get_dict(), expected, np_allclose=True) == {}
