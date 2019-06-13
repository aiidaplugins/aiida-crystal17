import os  # noqa: F401
from jsonextended import edict
from aiida_crystal17 import __version__
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401
from aiida_crystal17.tests import TEST_DIR  # noqa: F401
from aiida_crystal17.gulp.parsers.write_input import (  # noqa: F401
    InputCreationSingle, InputCreationOpt)
from aiida_crystal17.symmetry import convert_structure


def write_input_file(icreate, file_like, structure, potential,
                     parameters=None, symmetry=None):
    icreate.create_content(structure, potential, parameters, symmetry)
    icreate.write_content(file_like)
    return icreate.get_content_hash()


def get_pyrite_structure():
    structure_data = {
        "lattice": [[5.38, 0.000000, 0.000000],
                    [0.000000, 5.38, 0.000000],
                    [0.000000, 0.000000, 5.38]],
        "fcoords": [[0.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.5],
                    [0.5, 0.5, 0.0], [0.338, 0.338, 0.338],
                    [0.662, 0.662, 0.662], [0.162, 0.662, 0.838],
                    [0.838, 0.338, 0.162], [0.662, 0.838, 0.162],
                    [0.338, 0.162, 0.838], [0.838, 0.162, 0.662],
                    [0.162, 0.838, 0.338]],
        "symbols": ['Fe'] * 4 + ['S'] * 8,
        "pbc": [True, True, True]
    }
    return convert_structure(structure_data, "aiida")


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


def test_run_single_lj(db_test_app):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    structure = get_pyrite_structure()
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


def test_run_optimize_lj(db_test_app):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    structure = get_pyrite_structure()
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
