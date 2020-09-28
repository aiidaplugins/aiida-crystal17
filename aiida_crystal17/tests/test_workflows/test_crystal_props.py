import sys

from aiida.cmdline.utils.common import get_workchain_report  # noqa: F401
from aiida.engine import run_get_node
from aiida.orm import Dict, SinglefileData
import pytest

from aiida_crystal17.data.input_params import CryInputParamsData
from aiida_crystal17.tests import open_resource_binary
from aiida_crystal17.tests.utils import AiidaTestApp, sanitize_calc_info  # noqa: F401
from aiida_crystal17.workflows.crystal_props.base import CryPropertiesWorkChain


def clear_spec():
    # TODO this is required while awaiting fix for aiidateam/aiida-core#3143
    if hasattr(CryPropertiesWorkChain, "_spec"):
        del CryPropertiesWorkChain._spec


def get_parameters():
    return {
        "scf": CryInputParamsData(
            data={
                "title": "MgO Bulk",
                "scf": {"k_points": [8, 8], "post_scf": ["PPAN"]},
            }
        ),
        "doss": Dict(
            dict={
                "k_points": [18, 36],
                "npoints": 100,
                "band_minimum": -10,
                "band_maximum": 10,
                "band_units": "eV",
            }
        ),
        "ech3": Dict(
            dict={
                "npoints": 20,
            }
        ),
    }


def test_builder_empty(db_test_app):
    clear_spec()
    wc_builder = CryPropertiesWorkChain.get_builder()
    db_test_app.generate_context(CryPropertiesWorkChain, wc_builder, [])


def test_builder_bad_inputs(db_test_app):
    clear_spec()
    wc_builder = CryPropertiesWorkChain.get_builder()
    with pytest.raises(Exception):
        wc_builder.doss.parameters = Dict()
    wc_builder.doss.parameters = get_parameters()["doss"]
    with pytest.raises(Exception):
        db_test_app.generate_context(CryPropertiesWorkChain, wc_builder, [])


def test_builder_populated(db_test_app):
    clear_spec()
    wc_builder = CryPropertiesWorkChain.get_builder()
    with open_resource_binary("doss", "mgo_sto3g_scf", "fort.9") as handle:
        wc_builder.wf_folder = SinglefileData(handle)
    wc_builder.doss.code = db_test_app.get_or_create_code("crystal17.doss")
    wc_builder.doss.parameters = get_parameters()["doss"]
    wc_builder.doss.metadata = db_test_app.get_default_metadata()
    db_test_app.generate_context(CryPropertiesWorkChain, wc_builder, [])


def test_init_steps(db_test_app, data_regression):
    clear_spec()
    wc_builder = CryPropertiesWorkChain.get_builder()
    with open_resource_binary("doss", "mgo_sto3g_scf", "fort.9") as handle:
        wc_builder.wf_folder = SinglefileData(handle)
    wc_builder.doss.code = db_test_app.get_or_create_code("crystal17.doss")
    wc_builder.doss.parameters = get_parameters()["doss"]
    wc_builder.doss.metadata = db_test_app.get_default_metadata()
    wc_builder.test_run = True
    steps = ["check_inputs", "check_wf_folder"]
    wkchain, step_outcomes, context = db_test_app.generate_context(
        CryPropertiesWorkChain, wc_builder, steps
    )

    data_regression.check(context)
    try:
        assert step_outcomes[0] is None
        assert step_outcomes[1] is False
    except Exception:
        sys.stderr.write(get_workchain_report(wkchain, "REPORT"))
        raise


@pytest.mark.cry17_calls_executable
def test_run_prop_mgo_no_scf(db_test_app, sanitise_calc_attr, data_regression):
    """Test the workchains when a folder is supplied that contains the wavefunction file."""
    clear_spec()

    wc_builder = CryPropertiesWorkChain.get_builder()

    with open_resource_binary("doss", "mgo_sto3g_scf", "fort.9") as handle:
        wc_builder.wf_folder = SinglefileData(handle)

    wc_builder.doss.code = db_test_app.get_or_create_code("crystal17.doss")
    wc_builder.doss.parameters = get_parameters()["doss"]
    wc_builder.doss.metadata = db_test_app.get_default_metadata()

    wc_builder.ech3.code = db_test_app.get_or_create_code("crystal17.ech3")
    wc_builder.ech3.parameters = get_parameters()["ech3"]
    wc_builder.ech3.metadata = db_test_app.get_default_metadata()

    outputs, wc_node = run_get_node(wc_builder)
    sys.stderr.write(get_workchain_report(wc_node, "REPORT"))

    wk_attributes = sanitise_calc_attr(wc_node.attributes)

    data_regression.check(
        {
            "calc_node": wk_attributes,
            "incoming": sorted(wc_node.get_incoming().all_link_labels()),
            "outgoing": sorted(wc_node.get_outgoing().all_link_labels()),
            # "results": outputs["results"].attributes
        }
    )


@pytest.mark.cry17_calls_executable
def test_run_prop_mgo_with_scf(
    db_test_app, get_structure_and_symm, upload_basis_set_family, sanitise_calc_attr, data_regression
):
    """Test the workchains when computation inputs are supplied to calculate the wavefunction."""
    clear_spec()

    wc_builder = CryPropertiesWorkChain.get_builder()

    structure, symmetry = get_structure_and_symm("MgO")
    wc_builder.scf.code = db_test_app.get_or_create_code("crystal17.main")
    wc_builder.scf.structure = structure
    wc_builder.scf.symmetry = symmetry
    wc_builder.scf.parameters = get_parameters()["scf"]
    wc_builder.scf.basissets = {
        k: v for k, v in upload_basis_set_family().items() if k in ["Mg", "O"]
    }
    wc_builder.scf.metadata = db_test_app.get_default_metadata()

    wc_builder.doss.code = db_test_app.get_or_create_code("crystal17.doss")
    wc_builder.doss.parameters = get_parameters()["doss"]
    wc_builder.doss.metadata = db_test_app.get_default_metadata()

    wc_builder.clean_workdir = True

    outputs, wc_node = run_get_node(wc_builder)
    sys.stderr.write(get_workchain_report(wc_node, "REPORT"))

    wk_attributes = sanitise_calc_attr(wc_node.attributes)

    data_regression.check(
        {
            "calc_node": wk_attributes,
            "incoming": sorted(wc_node.get_incoming().all_link_labels()),
            "outgoing": sorted(wc_node.get_outgoing().all_link_labels()),
            # "results": outputs["results"].attributes
        }
    )
