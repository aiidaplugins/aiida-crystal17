import os  # noqa: F401
from jsonextended import edict
from aiida_crystal17 import __version__
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401
from aiida_crystal17.tests import TEST_DIR  # noqa: F401
from aiida_crystal17.gulp.parsers.write_input import (  # noqa: F401
    InputCreationSingle, InputCreationOpt)
from aiida_crystal17.symmetry import compute_symmetry_dict


def write_input_file(icreate, file_like, structure, potential,
                     parameters=None, symmetry=None):
    icreate.create_content(structure, potential, parameters, symmetry)
    icreate.write_content(file_like)
    return icreate.get_content_hash()


def get_pyrite_potential_lj():
    return {
        "pair_style": "lj",
        "data": {
            "atoms": {
                "Fe": {
                    "Fe": {
                        "A": 1.0,
                        "B": 1.0,
                        "rmax": 12.0
                    },
                    "S": {
                        "A": 1.0,
                        "B": 1.0,
                        "rmax": 12.0
                    }
                },
                "S": {
                    "S": {
                        "A": 1.0,
                        "B": 1.0,
                        "rmax": 12.0
                    }
                }
            }
        }
    }


def test_run_single_lj(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    structure = get_structure("pyrite")
    potential = db_test_app.get_data_node("dict",
                                          dict=get_pyrite_potential_lj())

    # file_hash = write_input_file(
    #     InputCreationSingle(),
    #     os.path.join(TEST_DIR, "gulp_input_files", "single_lj_pyrite.gin"),
    #     structure, potential)
    # raise ValueError(file_hash)

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
    builder.structure = structure
    builder.potential = potential

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


def test_run_optimize_lj(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    structure = get_structure("pyrite")
    potential = db_test_app.get_data_node("dict",
                                          dict=get_pyrite_potential_lj())
    parameters = db_test_app.get_data_node(
        "dict", dict={
            "minimize": {"style": "cg", "max_iterations": 100},
            "relax": {"type": "conp"}})

    # file_hash = write_input_file(
    #     InputCreationOpt({"cif": "output.cif"}),
    #     os.path.join(TEST_DIR, "gulp_input_files", "optimize_lj_pyrite.gin"),
    #     structure, potential, parameters=parameters)
    # raise ValueError(file_hash)

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
    builder.potential = potential
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


def test_run_optimize_lj_with_symm(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node
    from aiida.plugins import DataFactory

    structure = get_structure("pyrite")
    symmetry = DataFactory('crystal17.symmetry')(
        data=compute_symmetry_dict(structure, 0.01, None))
    potential = db_test_app.get_data_node("dict",
                                          dict=get_pyrite_potential_lj())
    parameters = db_test_app.get_data_node(
        "dict", dict={
            "minimize": {"style": "cg", "max_iterations": 100},
            "relax": {"type": "conp"}})

    # file_hash = write_input_file(
    #     InputCreationOpt({"cif": "output.cif"}),
    #     os.path.join(TEST_DIR, "gulp_input_files", "optimize_lj_pyrite_symm.gin"),
    #     structure, potential, parameters=parameters, symmetry=symmetry)
    # raise ValueError(file_hash)

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
    builder.potential = potential
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
