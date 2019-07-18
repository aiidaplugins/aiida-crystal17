""" Tests for main CRYSTAL17 calculation

"""
import os
from textwrap import dedent

import pytest
from aiida.engine import run_get_node
from aiida.orm import Dict, RemoteData
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_calcjob_submit_mgo(db_test_app):
    # type: (AiidaTestApp, bool) -> None
    """Test submitting a calculation"""

    code = db_test_app.get_or_create_code('crystal17.doss')
    remote = RemoteData(
        remote_path=os.path.join(TEST_FILES, "doss", "mgo_sto3g_scf"),
        computer=db_test_app.get_or_create_computer())

    # set up calculation
    builder = code.get_builder()
    builder.metadata = {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 30,
            "input_wf_name": "fort.9"
        },
        "dry_run": True
    }
    builder.parameters = Dict(dict={
        "shrink_is": 18,
        "shrink_isp": 36,
        "npoints": 100,
        "band_minimum": -10,
        "band_maximum": 10,
        "band_units": "eV"
    })
    builder.wf_folder = remote

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.doss', folder, builder)

        # Check the attributes of the returned `CalcInfo`
        assert calc_info.codes_info[0].cmdline_params == []
        assert sorted(calc_info.local_copy_list) == sorted([])
        assert sorted(calc_info.retrieve_list) == sorted(['main.out', 'fort.25'])
        assert sorted(calc_info.retrieve_temporary_list) == sorted([])

        assert sorted(folder.get_content_list()) == sorted([
            process_options.input_file_name
        ])

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()

    expected_input = dedent("""\
        NEWK
        18 36
        1 0
        DOSS
        0 100 -1 -1 1 14 0
        -0.36749322 0.36749322
        END""")

    assert input_content == expected_input


@pytest.mark.process_execution
def test_run_mgo_scf(db_test_app, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation"""

    code = db_test_app.get_or_create_code('crystal17.doss')
    remote = RemoteData(
        remote_path=os.path.join(TEST_FILES, "doss", "mgo_sto3g_scf"),
        computer=db_test_app.get_or_create_computer())

    # set up calculation
    builder = code.get_builder()
    builder.metadata = {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 30,
            "input_wf_name": "fort.9"
        }
    }
    builder.parameters = Dict(dict={
        "shrink_is": 18,
        "shrink_isp": 36,
        "npoints": 100,
        "band_minimum": -10,
        "band_maximum": 10,
        "band_units": "eV"
    })
    builder.wf_folder = remote

    output = run_get_node(builder)
    calc_node = output.node

    db_test_app.check_calculation(
        calc_node, ["results", "arrays"])

    calc_attributes = calc_node.attributes
    calc_attributes.pop("job_id", None)
    calc_attributes.pop("scheduler_lastchecktime", None)
    calc_attributes.pop("last_jobinfo", None)
    calc_attributes.pop("remote_workdir", None)
    calc_attributes.pop("retrieve_singlefile_list", None)

    results = {k: round(i, 7) if isinstance(i, float) else i
               for k, i in calc_node.outputs.results.attributes.items()}

    data_regression.check({
        "calc": calc_attributes,
        "results": results,
        "arrays": calc_node.outputs.arrays.attributes
    })
