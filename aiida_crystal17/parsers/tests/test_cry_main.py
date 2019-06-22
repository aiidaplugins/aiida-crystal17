import os
import pytest
from aiida.orm import FolderData
# from aiida.cmdline.utils.common import get_calcjob_report
from aiida_crystal17.tests import TEST_DIR


@pytest.mark.parametrize('plugin_name', [
    "crystal17.main",
])
def test_missing_output(db_test_app, plugin_name):

    retrieved = FolderData()

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    parser = db_test_app.get_parser_cls(plugin_name)
    results, calcfunction = parser.parse_from_node(calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_OUTPUT_FILE_MISSING.status


@pytest.mark.parametrize('plugin_name', [
    "crystal17.main",
])
def test_empty_output(db_test_app, plugin_name):

    retrieved = FolderData()
    with retrieved.open('main.out', 'w'):
        pass

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    parser = db_test_app.get_parser_cls(plugin_name)
    results, calcfunction = parser.parse_from_node(calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.ERROR_OUTPUT_PARSING.status


@pytest.mark.parametrize('plugin_name', [
    "crystal17.main",
])
def test_failed_scf_convergence(db_test_app, plugin_name):

    retrieved = FolderData()
    retrieved.put_object_from_file(os.path.join(
        TEST_DIR, "output_files", "FAILED_SCF_bcc_iron.crystal.out"), "main.out")

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    parser = db_test_app.get_parser_cls(plugin_name)
    results, calcfunction = parser.parse_from_node(calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.UNCONVERGED_SCF.status


@pytest.mark.parametrize('plugin_name', [
    "crystal17.main",
])
def test_failed_geom_convergence(db_test_app, plugin_name):

    retrieved = FolderData()
    retrieved.put_object_from_file(os.path.join(
        TEST_DIR, "output_files", "FAILED_GEOM_mackinawite_opt.crystal.out"), "main.out")

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    parser = db_test_app.get_parser_cls(plugin_name)
    results, calcfunction = parser.parse_from_node(calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert calcfunction.exit_status == calc_node.process_class.exit_codes.UNCONVERGED_GEOMETRY.status
