""" Tests for basic CRYSTAL17 calculation

"""
import os

import pytest

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp, sanitize_calc_info  # noqa: F401
from aiida_crystal17.common import recursive_round


def test_calcjob_submission(db_test_app, data_regression):
    # type: (AiidaTestApp) -> None
    """Test submitting a calculation"""
    from aiida.plugins import DataFactory
    singlefile_data_cls = DataFactory('singlefile')

    # Prepare input parameters
    code = db_test_app.get_or_create_code('crystal17.basic')
    infile = singlefile_data_cls(
        file=os.path.join(TEST_FILES, "crystal", "mgo_sto3g_scf", 'INPUT'))
    infile.store()

    # set up calculation
    builder = code.get_builder()
    builder.metadata.options.withmpi = False
    builder.metadata.options.resources = {
        "num_machines": 1, "num_mpiprocs_per_machine": 1}
    builder.input_file = infile

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.basic', folder, builder)

    data_regression.check(sanitize_calc_info(calc_info))


@pytest.mark.parametrize("infolder,external_geom", (
    ('mgo_sto3g_scf', False),
    ('mgo_sto3g_opt', False),
    ('mgo_sto3g_scf_external', True)
))
@pytest.mark.process_execution
def test_calcjob_run(db_test_app, infolder, external_geom, data_regression):
    # type: (AiidaTestApp, str, str) -> None
    """Test running an optimisation calculation"""
    from aiida.engine import run_get_node
    from aiida.plugins import DataFactory
    singlefile_data_cls = DataFactory('singlefile')

    code = db_test_app.get_or_create_code('crystal17.basic')

    # set up calculation
    builder = code.get_builder()
    builder.metadata = {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 60
        }
    }
# .crystal.ingui # .crystal.d12
    # Prepare input parameters
    infile = singlefile_data_cls(
        file=os.path.join(TEST_FILES, "crystal", infolder, "INPUT"))
    builder.input_file = infile
    if external_geom:
        ingui = singlefile_data_cls(
            file=os.path.join(TEST_FILES, "crystal", infolder, "fort.34"))
        builder.input_external = ingui

    outcome = run_get_node(builder)
    # result = outcome.result
    calc_node = outcome.node

    db_test_app.check_calculation(
        calc_node, ["results", "structure", "symmetry"])

    results_attributes = calc_node.outputs.results.attributes
    results_attributes.pop("execution_time_seconds")
    results_attributes.pop("parser_version")
    results_attributes = recursive_round(results_attributes, 9)
    data_regression.check(results_attributes)

    data_regression.check(
        recursive_round(calc_node.outputs.structure.attributes, 9),
        "test_calcjob_run_{}_{}_struct".format(infolder, external_geom)
    )


def compare_symmetry():
    expected_ops = [
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    ]
    return expected_ops
