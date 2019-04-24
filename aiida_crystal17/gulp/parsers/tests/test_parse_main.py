import os
from aiida_crystal17.gulp.parsers.parse_main import (GulpSingleParser,
                                                     GulpOptParser)
from aiida_crystal17.tests import TEST_DIR
from aiida_crystal17.tests.aiida_test_app import AiidaTestApp  # noqa: F401


def test_single_no_file(db_test_app):
    # type: (AiidaTestApp) -> None
    from aiida.orm import FolderData
    retrieved = FolderData()
    parser = GulpSingleParser
    Calculation = db_test_app.get_calc_cls('gulp.single')
    node = db_test_app.generate_calcjob_node('gulp.single', retrieved)
    results, calcfunction = parser.parse_from_node(node)
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == Calculation.exit_codes.ERROR_OUTPUT_FILE_MISSING.status


def test_single(db_test_app):
    # type: (AiidaTestApp) -> None
    from aiida.orm import FolderData
    retrieved = FolderData()
    path = os.path.join(TEST_DIR, 'gulp_output_files', 'opt_reaxff_pyrite.gout')
    retrieved.put_object_from_file(path, "main.gout")
    parser = GulpSingleParser
    node = db_test_app.generate_calcjob_node('gulp.single', retrieved)
    results, calcfunction = parser.parse_from_node(node)
    assert calcfunction.is_finished_ok
    assert "results" in results


def test_optimize_no_file(db_test_app):
    # type: (AiidaTestApp) -> None
    from aiida.orm import FolderData
    retrieved = FolderData()
    parser = GulpOptParser
    Calculation = db_test_app.get_calc_cls('gulp.optimize')
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved)
    results, calcfunction = parser.parse_from_node(node)
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == Calculation.exit_codes.ERROR_OUTPUT_FILE_MISSING.status


def test_optimize_no_cif(db_test_app):
    # type: (AiidaTestApp) -> None
    from aiida.orm import FolderData
    retrieved = FolderData()
    path = os.path.join(TEST_DIR, 'gulp_output_files', 'opt_reaxff_pyrite.gout')
    Calculation = db_test_app.get_calc_cls('gulp.optimize')
    retrieved.put_object_from_file(path, "main.gout")
    parser = GulpOptParser
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved)
    results, calcfunction = parser.parse_from_node(node)
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == Calculation.exit_codes.ERROR_CIF_FILE_MISSING.status


def test_optimize(db_test_app):
    # type: (AiidaTestApp) -> None
    from aiida.orm import FolderData
    retrieved = FolderData()
    path = os.path.join(TEST_DIR, 'gulp_output_files', 'opt_reaxff_pyrite.gout')
    retrieved.put_object_from_file(path, "main.gout")
    path = os.path.join(TEST_DIR, 'gulp_output_files', 'opt_reaxff_pyrite.cif')
    retrieved.put_object_from_file(path, "output.cif")
    parser = GulpOptParser
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved)
    results, calcfunction = parser.parse_from_node(node)
    if not calcfunction.is_finished_ok:
        raise AssertionError(calcfunction.attributes)
    assert "results" in results
    assert "structure" in results

# TODO reaxff tests
