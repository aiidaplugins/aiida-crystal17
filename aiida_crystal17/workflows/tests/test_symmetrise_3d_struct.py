import pytest
from aiida.engine import run_get_node
from aiida.plugins import WorkflowFactory

from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_no_inputs(db_test_app):
    """test no inputs """
    with pytest.raises(ValueError):
        results, node = run_get_node(WorkflowFactory("crystal17.sym3d"))


def test_no_structure(db_test_app, data_regression):
    """test no inputs """
    results, node = run_get_node(
        WorkflowFactory("crystal17.sym3d"), symprec=0.01)
    data_regression.check(node.attributes)


def test_with_structure(db_test_app, get_structure, data_regression):
    """test no inputs """
    results, node = run_get_node(
        WorkflowFactory("crystal17.sym3d"), symprec=0.01,
        structure=get_structure("pyrite"))
    data_regression.check(node.attributes)
    assert "symmetry" in results


def test_with_cif(db_test_app, get_cif, data_regression):
    """test no inputs """
    results, node = run_get_node(
        WorkflowFactory("crystal17.sym3d"), symprec=0.01,
        cif=get_cif("pyrite"))
    data_regression.check(node.attributes)
    assert "symmetry" in results
