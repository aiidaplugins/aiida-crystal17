import os  # noqa: F401

from aiida.plugins import DataFactory

from aiida_crystal17.common import recursive_round
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401
from aiida_crystal17.tests import TEST_FILES  # noqa: F401
from aiida_crystal17.gulp.parsers.raw.write_input import (  # noqa: F401
    InputCreationSingle, InputCreationOpt)
from aiida_crystal17.symmetry import compute_symmetry_dict


def write_input_file(icreate, file_like, structure, potential, parameters=None, symmetry=None):
    icreate.create_content(structure, potential.get_input_lines(), parameters, symmetry)
    icreate.write_content(file_like)
    return icreate.get_content_hash()


def test_run_optimize_lj(db_test_app, get_structure, pyrite_potential_lj, data_regression):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    parameters = db_test_app.get_data_node('dict',
                                           dict={
                                               'minimize': {
                                                   'style': 'cg',
                                                   'max_iterations': 100
                                               },
                                               'relax': {
                                                   'type': 'conp'
                                               }
                                           })

    code = db_test_app.get_or_create_code('gulp.optimize')
    builder = code.get_builder()
    builder._update({
        'metadata': {
            'options': {
                'withmpi': False,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1,
                },
                'max_wallclock_seconds': 30
            }
        }
    })
    builder.structure = get_structure('pyrite')
    builder.potential = pyrite_potential_lj
    builder.parameters = parameters

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ['results', 'structure'])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)


def test_run_optimize_lj_with_symm(db_test_app, get_structure, pyrite_potential_lj, data_regression):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    structure = get_structure('pyrite')
    symmetry = DataFactory('crystal17.symmetry')(data=compute_symmetry_dict(structure, 0.01, None))
    parameters = db_test_app.get_data_node('dict',
                                           dict={
                                               'minimize': {
                                                   'style': 'cg',
                                                   'max_iterations': 100
                                               },
                                               'relax': {
                                                   'type': 'conp'
                                               }
                                           })

    code = db_test_app.get_or_create_code('gulp.optimize')
    builder = code.get_builder()
    builder._update({
        'metadata': {
            'options': {
                'withmpi': False,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1,
                },
                'max_wallclock_seconds': 30
            }
        }
    })
    builder.structure = structure
    builder.potential = pyrite_potential_lj
    builder.parameters = parameters
    builder.symmetry = symmetry

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ['results', 'structure', 'retrieved'])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)

    # file_regression.check(
    #     calc_node.outputs.retrieved.get_object_content('main.gout'), basename="optimize_lj_pyrite_symm.gout")
    # file_regression.check(
    #     calc_node.outputs.retrieved.get_object_content('main.gin'), basename="optimize_lj_pyrite_symm.gin")
    # file_regression.check(
    #     calc_node.outputs.retrieved.get_object_content('output.cif'), basename="optimize_lj_pyrite_symm.cif")


def test_run_optimize_reaxff(db_test_app, get_structure, pyrite_potential_reaxff, data_regression):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    parameters = db_test_app.get_data_node('dict',
                                           dict={
                                               'minimize': {
                                                   'style': 'cg',
                                                   'max_iterations': 100
                                               },
                                               'relax': {
                                                   'type': 'conp'
                                               }
                                           })

    code = db_test_app.get_or_create_code('gulp.optimize')
    builder = code.get_builder()
    builder._update({
        'metadata': {
            'options': {
                'withmpi': False,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1,
                },
                'max_wallclock_seconds': 30
            }
        }
    })
    builder.structure = get_structure('pyrite')
    builder.potential = pyrite_potential_reaxff
    builder.parameters = parameters

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ['results', 'structure'])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)


def test_run_optimize_reaxff_symm(db_test_app, get_structure, pyrite_potential_reaxff, data_regression):
    # type: (AiidaTestApp) -> None
    from aiida.engine import run_get_node

    parameters = db_test_app.get_data_node('dict',
                                           dict={
                                               'minimize': {
                                                   'style': 'cg',
                                                   'max_iterations': 100
                                               },
                                               'relax': {
                                                   'type': 'conp'
                                               }
                                           })

    code = db_test_app.get_or_create_code('gulp.optimize')
    builder = code.get_builder()
    builder._update({
        'metadata': {
            'options': {
                'withmpi': False,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1,
                },
                'max_wallclock_seconds': 30
            }
        }
    })
    builder.structure = get_structure('pyrite')
    builder.symmetry = DataFactory('crystal17.symmetry')(data=compute_symmetry_dict(builder.structure, 0.01, None))
    builder.potential = pyrite_potential_reaxff
    builder.parameters = parameters

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ['results', 'structure'])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)
