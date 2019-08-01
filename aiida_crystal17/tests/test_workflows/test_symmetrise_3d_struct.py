import pytest
from aiida.engine import run_get_node
from aiida.plugins import DataFactory, WorkflowFactory

from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401
from jsonschema.exceptions import ValidationError


def test_no_settings(db_test_app):
    """test no settings dict """
    with pytest.raises(ValueError):
        wflow_cls = WorkflowFactory('crystal17.sym3d')
        results, node = run_get_node(wflow_cls)


def test_bad_settings(db_test_app):
    """test bad settings dict """
    with pytest.raises(ValidationError):
        results, node = run_get_node(WorkflowFactory('crystal17.sym3d'), settings=DataFactory('dict')(dict={'a': 1}))


def test_no_structure(db_test_app):
    """test no StructureData or CifData """
    wflow_cls = WorkflowFactory('crystal17.sym3d')
    results, node = run_get_node(wflow_cls, settings=DataFactory('dict')(dict={'symprec': 0.01}))
    assert node.is_failed, node.exit_status
    assert node.exit_status == wflow_cls.exit_codes.ERROR_INVALID_INPUT_RESOURCES.status


def test_with_structure(db_test_app, get_structure, data_regression):
    """test computing symmetry from StructureData """
    results, node = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        settings=DataFactory('dict')(dict={
            'symprec': 0.01
        }),
        structure=get_structure('pyrite'))

    assert node.is_finished_ok, node.exit_status
    assert 'symmetry' in results
    assert 'structure' not in results
    attributes = results['symmetry'].attributes
    attributes['computation'].pop('symmetry_version')
    attributes['computation'].pop('computation_version')
    data_regression.check(attributes)


def test_with_cif(db_test_app, get_cif, data_regression):
    """test computing symmetry from CifData """
    results, node = run_get_node(
        WorkflowFactory('crystal17.sym3d'), settings=DataFactory('dict')(dict={
            'symprec': 0.01
        }), cif=get_cif('pyrite'))
    assert node.is_finished_ok, node.exit_status
    assert 'symmetry' in results
    assert 'structure' in results
    attributes = results['symmetry'].attributes
    attributes['computation'].pop('symmetry_version')
    attributes['computation'].pop('computation_version')
    data_regression.check(attributes)


@pytest.mark.parametrize('compute_primitive,standardize_cell', [(True, False), (False, True), (True, True)])
def test_symmetrise_structure(db_test_app, get_structure, compute_primitive, standardize_cell, data_regression):
    """symmetrising structure with different options """
    results, node = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        settings=DataFactory('dict')(dict={
            'symprec': 0.01,
            'compute_primitive': compute_primitive,
            'standardize_cell': standardize_cell
        }),
        structure=get_structure('zincblende'))
    # data_regression.check(node.attributes)
    assert node.is_finished_ok, node.exit_status
    assert 'symmetry' in results
    assert 'structure' in results
    attributes = results['symmetry'].attributes
    attributes['computation'].pop('symmetry_version')
    attributes['computation'].pop('computation_version')
    data_regression.check(attributes)


@pytest.mark.parametrize('compute_primitive', [True, False])
def test_new_kind_names(db_test_app, get_structure, compute_primitive, data_regression):
    """test add kind names to StructureData """
    results, node = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        settings=DataFactory('dict')(dict={
            'symprec': 0.01,
            'kind_names': ['Fe1', 'Fe1', 'Fe2', 'Fe2', 'S', 'S', 'S', 'S'],
            'compute_primitive': compute_primitive
        }),
        structure=get_structure('zincblende'))

    assert node.is_finished_ok, node.exit_status
    assert 'symmetry' in results
    assert 'structure' in results
    attributes = results['symmetry'].attributes
    attributes['computation'].pop('symmetry_version')
    attributes['computation'].pop('computation_version')
    data_regression.check(attributes)


def test_new_kind_names_fail(db_test_app, get_structure):
    """test add kind names to StructureData """
    wflow_cls = WorkflowFactory('crystal17.sym3d')
    results, node = run_get_node(
        wflow_cls,
        settings=DataFactory('dict')(dict={
            'symprec': 0.01,
            'kind_names': ['A']
        }),
        structure=get_structure('zincblende'))

    assert node.is_failed, node.exit_status
    assert node.exit_status == wflow_cls.exit_codes.ERROR_RESET_KIND_NAMES.status
