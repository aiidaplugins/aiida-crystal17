from io import StringIO

from aiida.orm import FolderData
import pytest

from aiida_crystal17.tests import open_resource_binary

# from aiida.cmdline.utils.common import get_calcjob_report


@pytest.mark.parametrize(
    "plugin_name",
    [
        "crystal17.newk",
    ],
)
def test_missing_output(db_test_app, plugin_name):

    retrieved = FolderData()

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert (
        calcfunction.exit_status
        == calc_node.process_class.exit_codes.ERROR_OUTPUT_FILE_MISSING.status
    )


@pytest.mark.parametrize(
    "plugin_name",
    [
        "crystal17.newk",
    ],
)
def test_empty_output(db_test_app, plugin_name):

    retrieved = FolderData()
    retrieved.put_object_from_filelike(StringIO(""), "main.out")

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert (
        calcfunction.exit_status
        == calc_node.process_class.exit_codes.ERROR_PARSING_STDOUT.status
    )


@pytest.mark.parametrize(
    "plugin_name",
    [
        "crystal17.newk",
    ],
)
def test_success(db_test_app, plugin_name, data_regression):

    retrieved = FolderData()
    with open_resource_binary(
        "doss", "cubic_rocksalt_orbitals", "cubic-rocksalt_2x1_pdos.doss.out"
    ) as handle:
        retrieved.put_object_from_filelike(handle, "main.out", mode="wb")

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    results, calcfunction = db_test_app.parse_from_node(plugin_name, calc_node)

    assert calcfunction.is_finished_ok, calcfunction.exception
    assert "results" in results
    results_attr = {
        k: round(i, 7) if isinstance(i, float) else i
        for k, i in results["results"].attributes.items()
    }
    data_regression.check({"results": results_attr})
