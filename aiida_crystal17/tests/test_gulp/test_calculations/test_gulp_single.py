# -*- coding: utf-8 -*-
from aiida.engine import run_get_node

from aiida_crystal17.common import recursive_round
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401
from aiida_crystal17.gulp.parsers.raw.write_input import (  # noqa: F401
    InputCreationSingle, InputCreationOpt)


def write_input_file(icreate, file_like, structure, potential, parameters=None, symmetry=None):
    icreate.create_content(structure, potential.get_input_lines(), parameters, symmetry)
    icreate.write_content(file_like)
    return icreate.get_content_hash()


def test_run_single_lj(db_test_app, get_structure, pyrite_potential_lj, data_regression):
    # type: (AiidaTestApp) -> None

    code = db_test_app.get_or_create_code('gulp.single')
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

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ['results'])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)


def test_run_single_reaxff(db_test_app, get_structure, pyrite_potential_reaxff_lowtol, data_regression):
    # type: (AiidaTestApp) -> None

    code = db_test_app.get_or_create_code('gulp.single')
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
    builder.potential = pyrite_potential_reaxff_lowtol

    calc_node = run_get_node(builder).node

    db_test_app.check_calculation(calc_node, ['results'])

    result = recursive_round(calc_node.outputs.results.get_dict(), 6)
    for key in ['parser_version', 'peak_dynamic_memory_mb', 'opt_time_second', 'total_time_second']:
        result.pop(key, None)
    data_regression.check(result)
