import pytest
from aiida.orm import FolderData
# from aiida.cmdline.utils.common import get_calcjob_report
from aiida_crystal17.common import recursive_round
from aiida_crystal17.tests import open_resource_binary


@pytest.mark.parametrize('plugin_name', [
    'crystal17.ech3',
])
def test_missing_stdout(db_test_app, plugin_name):

    retrieved = FolderData()

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_OUTPUT_FILE_MISSING.status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.ech3',
])
def test_empty_stdout(db_test_app, plugin_name):

    retrieved = FolderData()
    with retrieved.open('main.out', 'w'):
        pass
    with retrieved.open('DENS_CUBE.DAT', 'w'):
        pass

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_PARSING_STDOUT.status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.ech3',
])
def test_missing_isofile(db_test_app, plugin_name):

    retrieved = FolderData()
    with open_resource_binary('ech3', 'mgo_sto3g_scf', 'main.out') as handle:
        retrieved.put_object_from_filelike(handle, 'main.out', mode='wb')

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_DENSITY_FILE_MISSING.status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.ech3',
])
def test_empty_isofile(db_test_app, plugin_name):

    retrieved = FolderData()
    with open_resource_binary('ech3', 'mgo_sto3g_scf', 'main.out') as handle:
        retrieved.put_object_from_filelike(handle, 'main.out', mode='wb')
    with retrieved.open('DENS_CUBE.DAT', 'w'):
        pass

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_PARSING_DENSITY_FILE.status


@pytest.mark.parametrize('plugin_name', [
    'crystal17.ech3',
])
def test_success(db_test_app, plugin_name, data_regression):

    retrieved = FolderData()
    with open_resource_binary('ech3', 'mgo_sto3g_scf', 'main.out') as handle:
        retrieved.put_object_from_filelike(handle, 'main.out', mode='wb')
    with open_resource_binary('ech3', 'mgo_sto3g_scf', 'DENS_CUBE.DAT') as handle:
        retrieved.put_object_from_filelike(handle, 'DENS_CUBE.DAT', mode='wb')

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished_ok, calcfunction.exception
    assert 'results' in results
    results_attr = recursive_round(results['results'].attributes, 7)
    data_regression.check({'results': results_attr})
