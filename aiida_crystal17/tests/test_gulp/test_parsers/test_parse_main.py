# from aiida.cmdline.utils.common import get_calcjob_report
from aiida.orm import FolderData

from aiida_crystal17.tests import open_resource_binary
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
    with open_resource_binary('gulp', 'optimize_reaxff_pyrite', 'main.gout') as handle:
        retrieved.put_object_from_filelike(handle, 'main.gout', mode='wb')
    node = db_test_app.generate_calcjob_node('gulp.single', retrieved)
    results, calcfunction = db_test_app.parse_from_node('gulp.single', node)
    assert calcfunction.is_finished_ok
    assert 'results' in results


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
    calc_cls = db_test_app.get_calc_cls('gulp.optimize')
    retrieved = FolderData()
    with open_resource_binary('gulp', 'optimize_reaxff_pyrite', 'main.gout') as handle:
        retrieved.put_object_from_filelike(handle, 'main.gout', mode='wb')
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved)
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == calc_cls.exit_codes.ERROR_CIF_FILE_MISSING.status


def test_optimize_no_convergence(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    with open_resource_binary('gulp', 'failed', 'opt_step_limit.gout') as handle:
        retrieved.put_object_from_filelike(handle, 'main.gout', mode='wb')
    with open_resource_binary('gulp', 'optimize_reaxff_pyrite', 'output.cif') as handle:
        retrieved.put_object_from_filelike(handle, 'output.cif', mode='wb')
    calc_cls = db_test_app.get_calc_cls('gulp.optimize')
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved, options={'use_input_kinds': False})
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    # print(get_calcjob_report(node))
    # raise
    assert calcfunction.is_finished
    assert not calcfunction.is_finished_ok
    assert calcfunction.exit_status == calc_cls.exit_codes.ERROR_OPTIMISE_MAX_ATTEMPTS.status

    # the output structure should still be passed though
    assert 'results' in results
    assert 'structure' in results


def test_optimize_success(db_test_app):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    with open_resource_binary('gulp', 'optimize_reaxff_pyrite', 'main.gout') as handle:
        retrieved.put_object_from_filelike(handle, 'main.gout', mode='wb')
    with open_resource_binary('gulp', 'optimize_reaxff_pyrite', 'output.cif') as handle:
        retrieved.put_object_from_filelike(handle, 'output.cif', mode='wb')
    node = db_test_app.generate_calcjob_node('gulp.optimize', retrieved, options={'use_input_kinds': False})
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    if not calcfunction.is_finished_ok:
        raise AssertionError(calcfunction.attributes)
    assert 'results' in results
    assert 'structure' in results


def test_optimize_1d_molecule(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    retrieved = FolderData()
    with open_resource_binary('gulp', 's2_polymer_opt', 'main.gout') as handle:
        retrieved.put_object_from_filelike(handle, 'main.gout', mode='wb')

    node = db_test_app.generate_calcjob_node('gulp.optimize',
                                             retrieved,
                                             input_nodes={'structure': get_structure('s2_molecule')})
    results, calcfunction = db_test_app.parse_from_node('gulp.optimize', node)
    if not calcfunction.is_finished_ok:
        raise AssertionError(calcfunction.attributes)
    assert 'results' in results
    assert 'structure' in results
