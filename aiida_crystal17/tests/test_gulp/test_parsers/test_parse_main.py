import os

# from aiida.cmdline.utils.common import get_calcjob_report
from aiida.orm import FolderData

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_single_no_file(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    calc_cls = db_test_app.get_calc_cls('gulp.single')
    node = db_test_app.generate_calcjob_node('gulp.single', retrieved)
    results, calcfunction = db_test_app.parse_from_node('gulp.single', node)
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == calc_cls.exit_codes.ERROR_OUTPUT_FILE_MISSING.status


def test_single(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    path = os.path.join(TEST_FILES, "gulp", "optimize_reaxff_pyrite", 'main.gout')
    retrieved.put_object_from_file(path, "main.gout")
    node = db_test_app.generate_calcjob_node('gulp.single', retrieved)
    results, calcfunction = db_test_app.parse_from_node('gulp.single', node)
    assert calcfunction.is_finished_ok
    assert "results" in results


def test_optimize_no_file(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    calc_cls = db_test_app.get_calc_cls('gulp.optimize')
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved)
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == calc_cls.exit_codes.ERROR_OUTPUT_FILE_MISSING.status


def test_optimize_no_cif(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    path = os.path.join(TEST_FILES, "gulp", "optimize_reaxff_pyrite", 'main.gout')
    calc_cls = db_test_app.get_calc_cls('gulp.optimize')
    retrieved.put_object_from_file(path, "main.gout")
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved)
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == calc_cls.exit_codes.ERROR_CIF_FILE_MISSING.status


def test_optimize_no_convergence(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    path = os.path.join(TEST_FILES, "gulp", "failed", 'FAILED_OPT_main_out.gulp.out')
    retrieved.put_object_from_file(path, "main.gout")
    path = os.path.join(TEST_FILES, "gulp", "optimize_reaxff_pyrite", 'output.cif')
    calc_cls = db_test_app.get_calc_cls('gulp.optimize')
    retrieved.put_object_from_file(path, "output.cif")
    node = db_test_app.generate_calcjob_node(
        'gulp.optimize', retrieved, options={"use_input_kinds": False})
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    # print(get_calcjob_report(node))
    # raise
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == calc_cls.exit_codes.ERROR_NOT_OPTIMISED.status

    # the output structure should still be passed though
    assert "results" in results
    assert "structure" in results


def test_optimize_success(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    path = os.path.join(TEST_FILES, "gulp", "optimize_reaxff_pyrite", 'main.gout')
    retrieved.put_object_from_file(path, "main.gout")
    path = os.path.join(TEST_FILES, "gulp", "optimize_reaxff_pyrite", 'output.cif')
    retrieved.put_object_from_file(path, "output.cif")
    node = db_test_app.generate_calcjob_node(
        'gulp.optimize', retrieved, options={"use_input_kinds": False})
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    if not calcfunction.is_finished_ok:
        raise AssertionError(calcfunction.attributes)
    assert "results" in results
    assert "structure" in results

# TODO reaxff tests
