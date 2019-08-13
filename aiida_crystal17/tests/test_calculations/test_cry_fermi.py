"""Tests for main CRYSTAL17 calculation."""
import pytest

from aiida.engine import run_get_node
from aiida.orm import Int, RemoteData

from aiida_crystal17.tests import resource_context
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


@pytest.mark.cry17_calls_executable
def test_run_mgo_scf(db_test_app, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation."""
    metadata = {
        'options': {
            'withmpi': False,
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1,
            },
            'max_wallclock_seconds': 30,
            'input_wf_name': 'fort.9'
        }
    }

    # set up calculation
    builder = db_test_app.get_or_create_code('crystal17.fermi').get_builder()
    builder.metadata = metadata
    builder.shrink_is = Int(18)
    builder.shrink_isp = Int(36)

    with resource_context('fermi', 'mgo_sto3g_scf') as path:
        builder.wf_folder = RemoteData(remote_path=str(path), computer=db_test_app.get_or_create_computer())

        output = run_get_node(builder)
        calc_node = output.node

    db_test_app.check_calculation(calc_node, ['results', 'fermi_energy'])

    calc_attributes = calc_node.attributes
    calc_attributes.pop('job_id', None)
    calc_attributes.pop('scheduler_lastchecktime', None)
    calc_attributes.pop('last_jobinfo', None)
    calc_attributes.pop('remote_workdir', None)
    calc_attributes.pop('retrieve_singlefile_list', None)

    results = {k: round(i, 7) if isinstance(i, float) else i for k, i in calc_node.outputs.results.attributes.items()}

    data_regression.check({
        'calc': calc_attributes,
        'results': results,
        'fermi': round(calc_node.outputs.fermi_energy.value, 7)
    })
