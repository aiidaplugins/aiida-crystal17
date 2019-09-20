"""Tests for main CRYSTAL17 calculation."""
import pytest

from aiida.engine import run_get_node
from aiida.orm import Dict, FolderData, RemoteData, SinglefileData

from aiida_crystal17.tests import open_resource_binary, resource_context
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def get_metadata(dry_run=False):
    return {
        'options': {
            'withmpi': False,
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1,
            },
            'max_wallclock_seconds': 30,
            'input_wf_name': 'fort.9'
        },
        'dry_run': dry_run
    }


def test_calcjob_submit_mgo_remote(db_test_app):
    # type: (AiidaTestApp, bool) -> None
    """Test submitting a calculation, using a remote folder input for wf_input."""
    builder = db_test_app.get_or_create_code('crystal17.newk').get_builder()
    builder.metadata = get_metadata()
    builder.parameters = Dict(dict={'k_points': [18, 36]})

    with resource_context('newk', 'mgo_sto3g_scf', 'fort.9') as path:

        builder.wf_folder = RemoteData(remote_path=str(path), computer=db_test_app.get_or_create_computer())

        process_options = builder.process_class(inputs=builder).metadata.options

        with db_test_app.sandbox_folder() as folder:
            db_test_app.generate_calcinfo('crystal17.newk', folder, builder)
            assert folder.get_content_list() == [process_options.input_file_name]


def test_calcjob_submit_mgo_singlefile(db_test_app):
    # type: (AiidaTestApp, bool) -> None
    """Test submitting a calculation, using a singlefile input for wf_input."""
    builder = db_test_app.get_or_create_code('crystal17.newk').get_builder()
    builder.metadata = get_metadata()
    builder.parameters = Dict(dict={'k_points': [18, 36]})

    with open_resource_binary('newk', 'mgo_sto3g_scf', 'fort.9') as handle:
        builder.wf_folder = SinglefileData(handle)

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        db_test_app.generate_calcinfo('crystal17.newk', folder, builder)
        assert folder.get_content_list() == [process_options.input_file_name]


@pytest.mark.cry17_calls_executable
def test_run_mgo_scf_folder(db_test_app, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation."""
    # set up calculation
    builder = db_test_app.get_or_create_code('crystal17.newk').get_builder()
    builder.metadata = get_metadata()
    builder.parameters = Dict(dict={'k_points': [18, 36]})

    wf_folder = FolderData()
    with open_resource_binary('newk', 'mgo_sto3g_scf', 'fort.9') as handle:
        wf_folder.put_object_from_filelike(handle, 'fort.9', mode='wb')

    builder.wf_folder = wf_folder

    output = run_get_node(builder)
    calc_node = output.node

    db_test_app.check_calculation(calc_node, ['results'])

    calc_attributes = calc_node.attributes
    calc_attributes.pop('job_id', None)
    calc_attributes.pop('scheduler_lastchecktime', None)
    calc_attributes.pop('last_jobinfo', None)
    calc_attributes.pop('remote_workdir', None)
    calc_attributes.pop('retrieve_singlefile_list', None)

    results = {
        k: round(i, 7) if isinstance(i, float) else i
        for k, i in calc_node.outputs.results.attributes.items()
        if k not in ['execution_time_seconds']
    }

    data_regression.check({
        'calc': calc_attributes,
        'results': results,
    })
