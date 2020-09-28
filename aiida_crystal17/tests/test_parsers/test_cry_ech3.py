from io import StringIO

from aiida.orm import FolderData
import pytest

# from aiida.cmdline.utils.common import get_calcjob_report
from aiida_crystal17.common import recursive_round
from aiida_crystal17.tests import open_resource_binary, resource_context


@pytest.mark.parametrize(
    "plugin_name",
    [
        "crystal17.ech3",
    ],
)
def test_missing_stdout(db_test_app, plugin_name):

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
        "crystal17.ech3",
    ],
)
def test_empty_stdout(db_test_app, plugin_name):

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
        "crystal17.ech3",
    ],
)
def test_missing_density(db_test_app, plugin_name):

    retrieved = FolderData()
    with open_resource_binary("ech3", "mgo_sto3g_scf", "main.out") as handle:
        retrieved.put_object_from_filelike(handle, "main.out", mode="wb")

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    with db_test_app.sandbox_folder() as temp_folder:
        results, calcfunction = db_test_app.parse_from_node(
            plugin_name, calc_node, retrieved_temp=temp_folder.abspath
        )

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert (
        calcfunction.exit_status
        == calc_node.process_class.exit_codes.ERROR_DENSITY_FILE_MISSING.status
    )


@pytest.mark.parametrize(
    "plugin_name",
    [
        "crystal17.ech3",
    ],
)
def test_empty_density(db_test_app, plugin_name):

    retrieved = FolderData()
    with open_resource_binary("ech3", "mgo_sto3g_scf", "main.out") as handle:
        retrieved.put_object_from_filelike(handle, "main.out", mode="wb")

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    with db_test_app.sandbox_folder() as temp_folder:
        with temp_folder.open("DENS_CUBE.DAT", "w"):
            pass
        results, calcfunction = db_test_app.parse_from_node(
            plugin_name, calc_node, retrieved_temp=temp_folder.abspath
        )

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_failed, calcfunction.exit_status
    assert (
        calcfunction.exit_status
        == calc_node.process_class.exit_codes.ERROR_PARSING_DENSITY_FILE.status
    )


@pytest.mark.parametrize(
    "plugin_name",
    [
        "crystal17.ech3",
    ],
)
def test_success(db_test_app, plugin_name, data_regression):

    retrieved = FolderData()
    with open_resource_binary("ech3", "mgo_sto3g_scf", "main.out") as handle:
        retrieved.put_object_from_filelike(handle, "main.out", mode="wb")

    calc_node = db_test_app.generate_calcjob_node(plugin_name, retrieved)
    with resource_context("ech3", "mgo_sto3g_scf") as path:
        results, calcfunction = db_test_app.parse_from_node(
            plugin_name, calc_node, retrieved_temp=str(path)
        )

    assert calcfunction.is_finished_ok, calcfunction.exception
    assert "results" in results
    assert "charge" in results
    data_regression.check(
        {
            "results": recursive_round(results["results"].attributes, 7),
            "charge": recursive_round(results["charge"].attributes, 7),
        }
    )
