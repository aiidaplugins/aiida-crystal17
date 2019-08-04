import pytest
import six

from aiida.orm import FolderData
from aiida.cmdline.utils.common import get_calcjob_report  # noqa: F401
from aiida_crystal17.tests import open_resource_binary, resource_context


@pytest.mark.parametrize('plugin_name', [
    'crystal17.main',
])
def test_missing_output(db_test_app, plugin_name):

    retrieved = FolderData()

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_OUTPUT_FILE_MISSING.status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.main',
])
def test_empty_output(db_test_app, plugin_name):

    retrieved = FolderData()
    with retrieved.open('main.out', 'w'):
        pass

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_PARSING_STDOUT.status


@pytest.mark.parametrize('plugin_name,fcontent,error_msg', [
    ('crystal17.main', '=>> PBS: job killed: mem job total 1 kb exceeded limit 10 kb', 'ERROR_OUT_OF_MEMORY'),
    ('crystal17.main', '=>> PBS: job killed: vmem job total 1 kb exceeded limit 10 kb', 'ERROR_OUT_OF_VMEMORY'),
    ('crystal17.main', '=>> PBS: job killed: walltime 100 exceeded limit 10', 'ERROR_OUT_OF_WALLTIME'),
])
def test_failed_pbs(db_test_app, plugin_name, fcontent, error_msg):

    retrieved = FolderData()
    with retrieved.open('_scheduler-stderr.txt', 'w') as handle:
        handle.write(six.ensure_text(fcontent))

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes[error_msg].status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.main',
])
def test_failed_scf_convergence(db_test_app, plugin_name):

    retrieved = FolderData()
    with open_resource_binary('crystal', 'failed', 'FAILED_SCF_bcc_iron.out') as handle:
        retrieved.put_object_from_filelike(handle, 'main.out', mode='wb')

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.UNCONVERGED_SCF.status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.main',
])
def test_failed_geom_convergence(db_test_app, plugin_name):

    retrieved = FolderData()
    with open_resource_binary('crystal', 'failed', 'FAILED_GEOM_mackinawite_opt.out') as handle:
        retrieved.put_object_from_filelike(handle, 'main.out', mode='wb')

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.UNCONVERGED_GEOMETRY.status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.main',
])
def test_failed_optimisation(db_test_app, plugin_name, data_regression):
    """Test that if the optimisation is killed before completion, the trajectory data is still available."""
    retrieved = FolderData()
    with open_resource_binary('crystal', 'nio_sto3g_afm_opt_walltime', 'main.out') as handle:
        retrieved.put_object_from_filelike(handle, 'main.out', mode='wb')
    with open_resource_binary('crystal', 'nio_sto3g_afm_opt_walltime', '_scheduler-stderr.txt') as handle:
        retrieved.put_object_from_filelike(handle, '_scheduler-stderr.txt', mode='wb')

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)

    with resource_context('crystal', 'nio_sto3g_afm_opt_walltime') as path:
        results, calcfunction = db_test_app.parse_from_node(plugin_name,
                                                            calc_node,
                                                            retrieved_temporary_folder=str(path))

    # print(get_calcjob_report(calc_node))

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_OUT_OF_WALLTIME.status

    assert 'optimisation' in results, results
    data_regression.check(results['optimisation'].attributes)
