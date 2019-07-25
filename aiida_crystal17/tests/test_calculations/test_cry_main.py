""" Tests for main CRYSTAL17 calculation

"""
import os

import pytest

from aiida import orm
from aiida.engine import run_get_node
from aiida.cmdline.utils.common import get_calcjob_report  # noqa: F401
from aiida.plugins import CalculationFactory, DataFactory, WorkflowFactory

from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp, sanitize_calc_info  # noqa: F401
from aiida_crystal17.common import recursive_round
from aiida_crystal17.data.kinds import KindData
from aiida_crystal17.data.basis_set import BasisSetData
from aiida_crystal17.data.input_params import CryInputParamsData


def test_create_builder(db_test_app, get_structure):
    """test preparation of inputs"""
    db_test_app.get_or_create_code('crystal17.main')

    inparams = {'scf.k_points': (8, 8)}

    instruct = get_structure('MgO')
    mg_basis, _ = BasisSetData.get_or_create(os.path.join(TEST_FILES, 'basis_sets', 'sto3g', 'sto3g_Mg.basis'))
    o_basis, _ = BasisSetData.get_or_create(os.path.join(TEST_FILES, 'basis_sets', 'sto3g', 'sto3g_O.basis'))

    sym_calc = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        structure=instruct,
        settings=DataFactory('dict')(dict={
            'symprec': 0.01,
            'compute_primitive': True
        })).node
    instruct = sym_calc.get_outgoing().get_node_by_label('structure')
    symmetry = sym_calc.get_outgoing().get_node_by_label('symmetry')

    calc_cls = CalculationFactory('crystal17.main')
    builder = calc_cls.create_builder(
        inparams, instruct, {
            'O': o_basis,
            'Mg': mg_basis
        }, symmetry=symmetry, unflatten=True)

    assert isinstance(builder.structure, orm.StructureData)
    builder.parameters


@pytest.mark.parametrize('input_symmetry', (False, True))
def test_calcjob_submit_mgo(db_test_app, input_symmetry, get_structure, data_regression, file_regression):
    """Test submitting a calculation"""

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    inparams = CryInputParamsData(data={'title': 'MgO Bulk', 'scf': {'k_points': (8, 8)}})

    instruct = get_structure('MgO')

    sym_calc = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        structure=instruct,
        settings=orm.Dict(dict={
            'symprec': 0.01,
            'compute_primitive': True
        })).node
    instruct = sym_calc.get_outgoing().get_node_by_label('structure')
    symmetry = sym_calc.get_outgoing().get_node_by_label('symmetry')

    mg_basis, _ = BasisSetData.get_or_create(os.path.join(TEST_FILES, 'basis_sets', 'sto3g', 'sto3g_Mg.basis'))
    o_basis, _ = BasisSetData.get_or_create(os.path.join(TEST_FILES, 'basis_sets', 'sto3g', 'sto3g_O.basis'))

    # set up calculation
    builder = code.get_builder()
    builder.metadata = db_test_app.get_default_metadata(dry_run=True)
    builder.parameters = inparams
    builder.structure = instruct
    builder.basissets = {'Mg': mg_basis, 'O': o_basis}
    if input_symmetry:
        builder.symmetry = symmetry

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo('crystal17.main', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()
        with folder.open('fort.34') as f:
            gui_content = f.read()  # noqa: F841
            # TODO test fort.34 (but rounded)

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


def test_calcjob_submit_nio_afm(db_test_app, get_structure, upload_basis_set_family, data_regression, file_regression):
    """Test submitting a calculation"""

    # get code
    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        'title': 'NiO Bulk with AFM spin',
        'scf.single': 'UHF',
        'scf.k_points': (8, 8),
        'scf.spinlock.SPINLOCK': (0, 15),
        'scf.numerical.FMIXING': 30,
        'scf.post_scf': ['PPAN']
    }

    instruct = get_structure('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    sym_calc = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        structure=instruct,
        settings=orm.Dict(dict={
            'symprec': 0.01,
            'compute_primitive': True
        })).node
    instruct = sym_calc.get_outgoing().get_node_by_label('structure')
    symmetry = sym_calc.get_outgoing().get_node_by_label('symmetry')

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params,
        instruct,
        'sto3g',
        symmetry=symmetry,
        kinds=kind_data,
        code=code,
        metadata=db_test_app.get_default_metadata(dry_run=True),
        unflatten=True)

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo('crystal17.main', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()
        with folder.open('fort.34') as f:
            gui_content = f.read()  # noqa: F841
            # TODO test fort.34 (but rounded)

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


def test_restart_wf_submit(db_test_app, get_structure, upload_basis_set_family, file_regression, data_regression):
    """ test restarting from a previous fort.9 file"""
    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        'title': 'NiO Bulk with AFM spin',
        'scf.single': 'UHF',
        'scf.k_points': (8, 8),
        'scf.spinlock.SPINLOCK': (0, 15),
        'scf.numerical.FMIXING': 30,
        'scf.post_scf': ['PPAN']
    }

    instruct = get_structure('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    sym_calc = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        structure=instruct,
        settings=DataFactory('dict')(dict={
            'symprec': 0.01,
            'compute_primitive': True
        })).node
    instruct = sym_calc.get_outgoing().get_node_by_label('structure')
    symmetry = sym_calc.get_outgoing().get_node_by_label('symmetry')

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params,
        instruct,
        'sto3g',
        symmetry=symmetry,
        kinds=kind_data,
        code=code,
        metadata=db_test_app.get_default_metadata(with_mpi=True),
        unflatten=True)

    remote = orm.RemoteData(
        computer=code.computer, remote_path=os.path.join(TEST_FILES, 'crystal', 'nio_sto3g_afm_scf_maxcyc'))
    builder.wf_folder = remote

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo('crystal17.main', folder, builder)
        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


@pytest.mark.process_execution
def test_run_nio_afm_scf(db_test_app, get_structure, upload_basis_set_family, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation"""

    # get code
    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        'title': 'NiO Bulk with AFM spin',
        'scf.single': 'UHF',
        'scf.k_points': (8, 8),
        'scf.spinlock.SPINLOCK': (0, 15),
        'scf.numerical.FMIXING': 30,
        'scf.post_scf': ['PPAN']
    }

    instruct = get_structure('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    sym_calc = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        structure=instruct,
        settings=orm.Dict(dict={
            'symprec': 0.01,
            'compute_primitive': True
        })).node
    instruct = sym_calc.get_outgoing().get_node_by_label('structure')
    symmetry = sym_calc.get_outgoing().get_node_by_label('symmetry')

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    metadata = {
        'options': {
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            },
            'withmpi': False,
            'max_wallclock_seconds': 30,
        }
    }
    builder = process_class.create_builder(
        params, instruct, 'sto3g', symmetry=symmetry, kinds=kind_data, code=code, metadata=metadata, unflatten=True)

    output = run_get_node(builder)
    calc_node = output.node

    db_test_app.check_calculation(calc_node, ['results'])

    results_attributes = calc_node.outputs.results.attributes
    results_attributes.pop('execution_time_seconds')
    results_attributes.pop('parser_version')
    results_attributes = recursive_round(results_attributes, 9)
    data_regression.check(results_attributes)


@pytest.mark.process_execution
@pytest.mark.skipif(
    os.environ.get('MOCK_CRY17_EXECUTABLES', True) != 'true', reason='the calculation takes about 50 minutes to run')
def test_run_nio_afm_fullopt(db_test_app, get_structure, upload_basis_set_family, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation"""

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        'title': 'NiO Bulk with AFM spin',
        'geometry.optimise.type': 'FULLOPTG',
        'scf.single': 'UHF',
        'scf.k_points': (8, 8),
        'scf.spinlock.SPINLOCK': (0, 15),
        'scf.numerical.FMIXING': 30,
        'scf.post_scf': ['PPAN']
    }

    instruct = get_structure('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    sym_calc = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        structure=instruct,
        settings=DataFactory('dict')(dict={
            'symprec': 0.01,
            'compute_primitive': True
        })).node
    instruct = sym_calc.get_outgoing().get_node_by_label('structure')
    symmetry = sym_calc.get_outgoing().get_node_by_label('symmetry')

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params,
        instruct,
        'sto3g',
        symmetry=symmetry,
        kinds=kind_data,
        code=code,
        metadata=db_test_app.get_default_metadata(),
        unflatten=True)

    output = run_get_node(builder)
    calc_node = output.node

    db_test_app.check_calculation(calc_node, ['results', 'structure'])

    results_attributes = calc_node.outputs.results.attributes
    results_attributes.pop('execution_time_seconds')
    results_attributes.pop('parser_version')
    results_attributes = recursive_round(results_attributes, 9)

    data_regression.check(results_attributes)

    data_regression.check(recursive_round(calc_node.outputs.structure.attributes, 9), 'test_run_nio_afm_fullopt_struct')


@pytest.mark.skipif(os.environ.get('MOCK_CRY17_EXECUTABLES', True) != 'true', reason='the calculation was run on a HPC')
def test_run_nio_afm_failed_opt(db_test_app, get_structure, upload_basis_set_family, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation where the optimisation fails,
    due to reaching walltime"""

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

    instruct = get_structure('NiO_afm')

    kind_data = KindData(data={
        'kind_names': ['Ni1', 'Ni2', 'O'],
        'spin_alpha': [True, False, False],
        'spin_beta': [False, True, False]
    })

    sym_calc = run_get_node(
        WorkflowFactory('crystal17.sym3d'),
        structure=instruct,
        settings=DataFactory('dict')(dict={
            'symprec': 0.01,
            'compute_primitive': True
        })).node
    instruct = sym_calc.get_outgoing().get_node_by_label('structure')
    symmetry = sym_calc.get_outgoing().get_node_by_label('symmetry')

    upload_basis_set_family()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params,
        instruct,
        'sto3g',
        symmetry=symmetry,
        kinds=kind_data,
        code=code,
        metadata=db_test_app.get_default_metadata(),
        unflatten=True)

    outputs, calc_node = run_get_node(builder)
    # print(get_calcjob_report(calc_node))
    assert 'optimisation' in outputs
    assert 'results' in outputs

    calc_attributes = calc_node.attributes
    for key in [
            'job_id', 'last_jobinfo', 'remote_workdir', 'scheduler_lastchecktime', 'retrieve_singlefile_list', 'version'
    ]:
        calc_attributes.pop(key, None)
    calc_attributes['retrieve_list'] = sorted(calc_attributes['retrieve_list'])

    results_attributes = outputs['results'].attributes
    results_attributes.pop('execution_time_seconds')
    results_attributes.pop('parser_version')
    results_attributes = recursive_round(results_attributes, 12)

    data_regression.check({
        'calc_node': calc_attributes,
        'outputs': sorted(outputs.keys()),
        'results': results_attributes,
        'optimisation': outputs['optimisation'].attributes
    })
