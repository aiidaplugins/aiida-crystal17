import os  # noqa: F401
from jsonextended import edict
from aiida.plugins import DataFactory
from aiida_crystal17 import __version__
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401
from aiida_crystal17.tests import TEST_FILES  # noqa: F401
from aiida_crystal17.gulp.parsers.raw.write_input import (  # noqa: F401
    InputCreationSingle, InputCreationOpt)
from aiida_crystal17.symmetry import compute_symmetry_dict


def write_input_file(icreate, file_like, structure, potential,
                     parameters=None, symmetry=None):
    icreate.create_content(structure, potential, parameters, symmetry)
    icreate.write_content(file_like)
    return icreate.get_content_hash()


def test_run_optimize_lj(db_test_app, get_structure, pyrite_potential_lj):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    parameters = db_test_app.get_data_node(
        "dict", dict={
            "minimize": {"style": "cg", "max_iterations": 100},
            "relax": {"type": "conp"}})

    code = db_test_app.get_or_create_code('gulp.optimize')
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
    builder.parameters = parameters

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ["results", "structure"])

    expected = {
        'energy_initial': -0.32809466,
        'optimised': True,
        'energy': -17.47113113,
        'energy_units': 'eV',
        'errors': [],
        'parser_class': 'GulpOptParser',
        'parser_errors': [],
        'parser_version': __version__,
        'parser_warnings': [],
        'warnings': []}
    assert edict.diff(
        calc_node.outputs.results.get_dict(), expected, np_allclose=True) == {}


def test_run_optimize_lj_with_symm(db_test_app, get_structure, pyrite_potential_lj):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    structure = get_structure("pyrite")
    symmetry = DataFactory('crystal17.symmetry')(
        data=compute_symmetry_dict(structure, 0.01, None))
    parameters = db_test_app.get_data_node(
        "dict", dict={
            "minimize": {"style": "cg", "max_iterations": 100},
            "relax": {"type": "conp"}})

    code = db_test_app.get_or_create_code('gulp.optimize')
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
    builder.structure = structure
    builder.potential = pyrite_potential_lj
    builder.parameters = parameters
    builder.symmetry = symmetry

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(
        calc_node, ["results", "structure", "retrieved"])

    expected = {
        'energy_initial': -0.32809466,
        'optimised': True,
        'energy': -14.12566776,
        'energy_units': 'eV',
        'errors': [],
        'parser_class': 'GulpOptParser',
        'parser_errors': [],
        'parser_version': __version__,
        'parser_warnings': [],
        'warnings': [("Conditions for a minimum have not been satisfied. "
                      "However no lower point can be found - treat results with caution")]}
    assert edict.diff(
        calc_node.outputs.results.get_dict(), expected, np_allclose=True) == {}

    # file_regression.check(
    #     calc_node.outputs.retrieved.get_object_content('main.gout'), basename="optimize_lj_pyrite_symm.gout")
    # file_regression.check(
    #     calc_node.outputs.retrieved.get_object_content('main.gin'), basename="optimize_lj_pyrite_symm.gin")
    # file_regression.check(
    #     calc_node.outputs.retrieved.get_object_content('output.cif'), basename="optimize_lj_pyrite_symm.cif")


def test_run_optimize_reaxff(db_test_app, get_structure, pyrite_potential_reaxff):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    parameters = db_test_app.get_data_node(
        "dict", dict={
            "minimize": {"style": "cg", "max_iterations": 100},
            "relax": {"type": "conp"}})

    code = db_test_app.get_or_create_code('gulp.optimize')
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
    builder.potential = pyrite_potential_reaxff
    builder.parameters = parameters

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ["results", "structure"])

    expected = {
        'errors': [], 'warnings': [], 'parser_version': __version__,
        'parser_class': 'GulpOptParser', 'parser_warnings': [], 'parser_errors': [],
        'energy_units': 'eV',
        'energy_initial': -42.24545667,
        'energy': -43.56745576,
        'optimised': True,
        'energy_contributions': {
            'Bond': -70.24248892, 'Coulomb': -3.09559776, 'Torsion': 0.79779098,
            'Lone-Pair': 1.21245957, 'Conjugation': 0.0, 'Hydrogen Bond': 0.0,
            'Valence Angle': 14.8595733, 'van der Waals': 3.23506097,
            'Coordination (over)': 9.93440993, 'Charge Equilibration': -0.26866394,
            'Coordination (under)': 1.1e-07, 'Valence Angle Conjugation': 0.0,
            'Double-Bond Valence Angle Penalty': 0.0}}
    assert edict.diff(
        calc_node.outputs.results.get_dict(), expected, np_allclose=True) == {}


def test_run_optimize_reaxff_symm(db_test_app, get_structure, pyrite_potential_reaxff):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    parameters = db_test_app.get_data_node(
        "dict", dict={
            "minimize": {"style": "cg", "max_iterations": 100},
            "relax": {"type": "conp"}})

    code = db_test_app.get_or_create_code('gulp.optimize')
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
    builder.symmetry = DataFactory('crystal17.symmetry')(
        data=compute_symmetry_dict(builder.structure, 0.01, None))
    builder.potential = pyrite_potential_reaxff
    builder.parameters = parameters

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ["results", "structure"])

    expected = {
        'errors': [], 'warnings': [], 'parser_version': __version__,
        'parser_class': 'GulpOptParser', 'parser_warnings': [], 'parser_errors': [],
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
        calc_node.outputs.results.get_dict(), expected, np_allclose=True) == {}
