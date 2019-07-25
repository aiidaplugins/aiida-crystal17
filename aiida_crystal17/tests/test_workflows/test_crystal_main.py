import os

import pytest

from aiida.engine import run_get_node
from aiida.cmdline.utils.common import get_workchain_report  # noqa: F401

from aiida_crystal17.tests.utils import AiidaTestApp, sanitize_calc_info  # noqa: F401
from aiida_crystal17.data.kinds import KindData

from aiida_crystal17.workflows.crystal_main.base import CryMainBaseWorkChain


def test_init_steps(db_test_app, get_structure_and_symm, upload_basis_set_family, data_regression):
    """ test the workchains initial setup and validation steps """
    if hasattr(CryMainBaseWorkChain, '_spec'):
        # TODO this is required while awaiting fix for aiidateam/aiida-core#3143
        del CryMainBaseWorkChain._spec

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        'title': 'NiO Bulk with AFM spin',
        'scf.single': 'UHF',
        'scf.k_points': (8, 8),
        'scf.spinlock.SPINLOCK': (0, 15),
        'scf.numerical.FMIXING': 50,
        'scf.numerical.MAXCYCLE': 10,
        'scf.post_scf': ['PPAN']
    }

    instruct, symmetry = get_structure_and_symm('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    calc_builder = process_class.create_builder(
        params,
        instruct,
        'sto3g',
        symmetry=symmetry,
        kinds=kind_data,
        code=code,
        metadata=db_test_app.get_default_metadata(),
        unflatten=True)

    wc_builder = CryMainBaseWorkChain.get_builder()
    wc_builder.cry = dict(calc_builder)
    wc_builder.clean_workdir = False
    wc_builder.kpoints_distance = 0.5
    wc_builder.kpoints_force_parity = True

    wkchain, step_outcomes, context = db_test_app.generate_context(
        CryMainBaseWorkChain, wc_builder, ['setup', 'validate_parameters', 'validate_basis_sets', 'validate_resources'])

    data_regression.check(context)

    assert all([o is None for o in step_outcomes])


@pytest.mark.process_execution
def test_base_nio_afm_scf_maxcyc(db_test_app, get_structure_and_symm, upload_basis_set_family, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation where the scf convergence fails, on the 1st iteration,
    due to reaching the maximum SCF cycles"""
    if hasattr(CryMainBaseWorkChain, '_spec'):
        # TODO this is required while awaiting fix for aiidateam/aiida-core#3143
        del CryMainBaseWorkChain._spec

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        'title': 'NiO Bulk with AFM spin',
        'scf.single': 'UHF',
        'scf.k_points': (8, 8),
        'scf.spinlock.SPINLOCK': (0, 15),
        'scf.numerical.FMIXING': 50,
        'scf.numerical.MAXCYCLE': 10,
        'scf.post_scf': ['PPAN']
    }

    instruct, symmetry = get_structure_and_symm('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    calc_builder = process_class.create_builder(
        params,
        instruct,
        'sto3g',
        symmetry=symmetry,
        kinds=kind_data,
        code=code,
        metadata=db_test_app.get_default_metadata(),
        unflatten=True)

    wc_builder = CryMainBaseWorkChain.get_builder()
    wc_builder.cry = dict(calc_builder)
    wc_builder.clean_workdir = False

    outputs, wc_node = run_get_node(wc_builder)
    print(get_workchain_report(wc_node, 'REPORT'))

    wk_attributes = wc_node.attributes
    for key in ['job_id', 'last_jobinfo', 'scheduler_lastchecktime', 'version']:
        wk_attributes.pop(key, None)

    data_regression.check({
        'calc_node': wk_attributes,
        'incoming': sorted(wc_node.get_incoming().all_link_labels()),
        'outgoing': sorted(wc_node.get_outgoing().all_link_labels()),
        # "results": outputs["results"].attributes
    })


@pytest.mark.process_execution
@pytest.mark.skipif(os.environ.get('MOCK_CRY17_EXECUTABLES', True) != 'true', reason='the calculation was run on a HPC')
def test_base_nio_afm_opt_walltime(db_test_app, get_structure_and_symm, upload_basis_set_family, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation where the optimisation fails, on the 1st iteration,
    due to reaching walltime """
    if hasattr(CryMainBaseWorkChain, '_spec'):
        # TODO this is required while awaiting fix for aiidateam/aiida-core#3143
        del CryMainBaseWorkChain._spec

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        'title': 'NiO Bulk with AFM spin',
        'geometry.optimise.type': 'FULLOPTG',
        'scf.single': 'UHF',
        'scf.k_points': (8, 8),
        'scf.spinlock.SPINLOCK': (0, 15),
        'scf.numerical.FMIXING': 50,
        'scf.post_scf': ['PPAN']
    }

    instruct, symmetry = get_structure_and_symm('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    upload_basis_set_family(group_name='sto3g2', stop_if_existing=False)

    # set up calculation
    process_class = code.get_builder().process_class
    calc_builder = process_class.create_builder(
        params,
        instruct,
        'sto3g2',
        symmetry=symmetry,
        kinds=kind_data,
        code=code,
        metadata=db_test_app.get_default_metadata(),  # with_mpi=True
        unflatten=True)

    wc_builder = CryMainBaseWorkChain.get_builder()
    wc_builder.cry = dict(calc_builder)
    wc_builder.clean_workdir = True

    outputs, wc_node = run_get_node(wc_builder)
    print(get_workchain_report(wc_node, 'REPORT'))

    wk_attributes = wc_node.attributes
    for key in ['job_id', 'last_jobinfo', 'scheduler_lastchecktime', 'version']:
        wk_attributes.pop(key, None)

    data_regression.check({
        'calc_node': wk_attributes,
        'incoming': sorted(wc_node.get_incoming().all_link_labels()),
        'outgoing': sorted(wc_node.get_outgoing().all_link_labels()),
        # "results": outputs["results"].attributes
    })
