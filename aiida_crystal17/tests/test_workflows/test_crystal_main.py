import os

import pytest

from aiida.engine import run_get_node
from aiida.cmdline.utils.common import get_workchain_report  # noqa: F401
from aiida.plugins import DataFactory, WorkflowFactory

from aiida_crystal17.tests.utils import AiidaTestApp, sanitize_calc_info  # noqa: F401
from aiida_crystal17.data.kinds import KindData

from aiida_crystal17.workflows.crystal_main.base import CryMainBaseWorkChain


@pytest.mark.process_execution
def test_base_nio_afm_scf_maxcyc(db_test_app, get_structure, upload_basis_set_family, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation where the scf convergence fails, on the 1st iteration,
    due to reaching the maximum SCF cycles"""

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 50,
        "scf.numerical.MAXCYCLE": 10,
        "scf.post_scf": ["PPAN"]
    }

    instruct = get_structure("NiO_afm")

    kind_data = KindData(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=DataFactory("dict")(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    calc_builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data, code=code,
        metadata=db_test_app.get_default_metadata(),
        unflatten=True)

    wc_builder = CryMainBaseWorkChain.get_builder()
    wc_builder.cry = dict(calc_builder)
    wc_builder.clean_workdir = False

    outputs, wc_node = run_get_node(wc_builder)
    print(get_workchain_report(wc_node, 'REPORT'))

    wk_attributes = wc_node.attributes
    for key in ["job_id", "last_jobinfo", "scheduler_lastchecktime"]:
        wk_attributes.pop(key, None)

    data_regression.check({
        "calc_node": wk_attributes,
        "incoming": sorted(wc_node.get_incoming().all_link_labels()),
        "outgoing": sorted(wc_node.get_outgoing().all_link_labels()),
        # "results": outputs["results"].attributes
    })


@pytest.mark.process_execution
@pytest.mark.skipif(os.environ.get("MOCK_CRY17_EXECUTABLES", True) != "true",
                    reason="the calculation was run on a HPC")
def test_base_nio_afm_opt_walltime(db_test_app, get_structure, upload_basis_set_family, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation where the optimisation fails, on the 1st iteration,
    due to reaching walltime"""

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "geometry.optimise.type": "FULLOPTG",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 50,
        "scf.post_scf": ["PPAN"]
    }

    instruct = get_structure("NiO_afm")

    kind_data = KindData(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=DataFactory("dict")(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    calc_builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data, code=code,
        metadata=db_test_app.get_default_metadata(),  # with_mpi=True
        unflatten=True)

    wc_builder = CryMainBaseWorkChain.get_builder()
    wc_builder.cry = dict(calc_builder)
    wc_builder.clean_workdir = False

    outputs, wc_node = run_get_node(wc_builder)
    print(get_workchain_report(wc_node, 'REPORT'))

    wk_attributes = wc_node.attributes
    for key in ["job_id", "last_jobinfo", "scheduler_lastchecktime"]:
        wk_attributes.pop(key, None)

    data_regression.check({
        "calc_node": wk_attributes,
        "incoming": sorted(wc_node.get_incoming().all_link_labels()),
        "outgoing": sorted(wc_node.get_outgoing().all_link_labels()),
        # "results": outputs["results"].attributes
    })
