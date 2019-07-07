""" Tests for main CRYSTAL17 calculation

"""
import os
from textwrap import dedent  # noqa: F401

import ejplugins
from jsonextended import edict
import pytest

from aiida import orm
from aiida.engine import run_get_node
from aiida.cmdline.utils.common import get_calcjob_report  # noqa: F401
from aiida.plugins import CalculationFactory, DataFactory, WorkflowFactory

import aiida_crystal17
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp, sanitize_calc_info  # noqa: F401
from aiida_crystal17.data.kinds import KindData
from aiida_crystal17.data.basis_set import BasisSetData
from aiida_crystal17.data.input_params import CryInputParamsData


def upload_basis_set_sto3g():
    """ upload the sto3g basis set"""
    BasisSetData.upload_basisset_family(
        os.path.join(TEST_FILES, "basis_sets", "sto3g"),
        "sto3g",
        "minimal basis sets",
        stop_if_existing=True,
        extension=".basis")


def test_create_builder(db_test_app, get_structure):
    """test preparation of inputs"""
    db_test_app.get_or_create_code('crystal17.main')

    inparams = {"scf.k_points": (8, 8)}

    instruct = get_structure("MgO")
    mg_basis, _ = BasisSetData.get_or_create(
        os.path.join(TEST_FILES, "basis_sets", "sto3g", 'sto3g_Mg.basis'))
    o_basis, _ = BasisSetData.get_or_create(
        os.path.join(TEST_FILES, "basis_sets", "sto3g", 'sto3g_O.basis'))

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=DataFactory("dict")(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    calc_cls = CalculationFactory('crystal17.main')
    builder = calc_cls.create_builder(
        inparams, instruct, {"O": o_basis, "Mg": mg_basis},
        symmetry=symmetry, unflatten=True)

    assert isinstance(builder.structure, orm.StructureData)
    builder.parameters


@pytest.mark.parametrize(
    "input_symmetry",
    (False, True)
)
def test_calcjob_submit_mgo(db_test_app, input_symmetry, get_structure,
                            data_regression, file_regression):
    """Test submitting a calculation"""

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    inparams = CryInputParamsData(data={
        "title": "MgO Bulk",
        "scf": {
            "k_points": (8, 8)
        }
    })

    instruct = get_structure("MgO")

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=orm.Dict(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    mg_basis, _ = BasisSetData.get_or_create(
        os.path.join(TEST_FILES, "basis_sets", "sto3g", 'sto3g_Mg.basis'))
    o_basis, _ = BasisSetData.get_or_create(
        os.path.join(TEST_FILES, "basis_sets", "sto3g", 'sto3g_O.basis'))

    # set up calculation
    builder = code.get_builder()
    builder.metadata = db_test_app.get_default_metadata(dry_run=True)
    builder.parameters = inparams
    builder.structure = instruct
    builder.basissets = {"Mg": mg_basis, "O": o_basis}
    if input_symmetry:
        builder.symmetry = symmetry

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.main', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()
        with folder.open('fort.34') as f:
            gui_content = f.read()  # noqa: F841
            # TODO test fort.34 (but rounded)

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


def test_calcjob_submit_nio_afm(db_test_app, get_structure,
                                data_regression, file_regression):
    """Test submitting a calculation"""

    # get code
    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 30,
        "scf.post_scf": ["PPAN"]
    }

    instruct = get_structure("NiO_afm")

    kind_data = KindData(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=orm.Dict(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basis_set_sto3g()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data, code=code,
        metadata=db_test_app.get_default_metadata(dry_run=True),
        unflatten=True)

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.main', folder, builder)

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()
        with folder.open('fort.34') as f:
            gui_content = f.read()  # noqa: F841
            # TODO test fort.34 (but rounded)

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


def test_restart_nio_afm_opt_submit(db_test_app, get_structure,
                                    file_regression, data_regression):

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "geometry.optimise.type": "FULLOPTG",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 30,
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

    upload_basis_set_sto3g()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data, code=code,
        metadata=db_test_app.get_default_metadata(with_mpi=True),
        unflatten=True)

    remote = orm.RemoteData(
        computer=code.computer,
        remote_path=os.path.join(TEST_FILES, "crystal", "nio_sto3g_afm_opt_walltime"))
    builder.parent_folder = remote

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.main', folder, builder)
        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()

    file_regression.check(input_content)
    data_regression.check(sanitize_calc_info(calc_info))


@pytest.mark.process_execution
def test_run_nio_afm_scf(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    """Test running a calculation"""

    # get code
    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 30,
        "scf.post_scf": ["PPAN"]
    }

    instruct = get_structure("NiO_afm")

    kind_data = KindData(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=orm.Dict(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basis_set_sto3g()

    # set up calculation
    process_class = code.get_builder().process_class
    metadata = {
        "options": {
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1
            },
            "withmpi": False,
            "max_wallclock_seconds": 30,
        }}
    builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data,
        code=code, metadata=metadata, unflatten=True)

    output = run_get_node(builder)
    calc_node = output.node

    db_test_app.check_calculation(
        calc_node, ["results"])

    expected_results = {
        'parser_version': str(aiida_crystal17.__version__),
        'ejplugins_version': str(ejplugins.__version__),
        'parser_class': 'CryMainParser',
        'parser_warnings': [],
        'parser_errors': [],
        'errors': [],
        'warnings': [],
        'number_of_atoms': 4,
        'energy': -85124.8936673389,
        'number_of_assymetric': 4,
        'volume': 36.099581472,
        'scf_iterations': 13,
        'energy_units': 'eV',
        'calculation_type': 'unrestricted open shell',
        # 'wall_time_seconds': 187,
        'calculation_spin': True,
        'mulliken_spin_total': 0.0,
        'mulliken_spins': [3.057, -3.057, -0.072, 0.072],
        'mulliken_electrons': [27.602, 27.603, 8.398, 8.397],
        'mulliken_charges': [0.398, 0.396999999999998, -0.398, -0.397]
    }

    result_node = calc_node.get_outgoing().get_node_by_label('results')
    attributes = result_node.get_dict()
    attributes.pop('wall_time_seconds', None)
    assert set(attributes.keys()) == set(expected_results.keys())
    assert edict.diff(attributes, expected_results, np_allclose=True) == {}


@pytest.mark.process_execution
@pytest.mark.skipif(os.environ.get("MOCK_CRY17_EXECUTABLES", True) != "true",
                    reason="the calculation takes about 50 minutes to run")
def test_run_nio_afm_fullopt(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    """Test running a calculation"""

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "geometry.optimise.type": "FULLOPTG",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 30,
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

    upload_basis_set_sto3g()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data, code=code,
        metadata=db_test_app.get_default_metadata(),
        unflatten=True)

    output = run_get_node(builder)
    calc_node = output.node

    db_test_app.check_calculation(
        calc_node, ["results", "structure"])

    expected_results = {
        'parser_version': str(aiida_crystal17.__version__),
        'ejplugins_version': str(ejplugins.__version__),
        'parser_class': 'CryMainParser',
        'parser_errors': [],
        'parser_warnings': [],
        'errors': [],
        'warnings':
        ['WARNING **** INT_SCREEN **** CELL PARAMETERS OPTIMIZATION ONLY'],
        'calculation_type': 'unrestricted open shell',
        'calculation_spin': True,
        # 'wall_time_seconds': 3018,
        'scf_iterations': 16,
        'opt_iterations': 19,
        'number_of_atoms': 4,
        'number_of_assymetric': 4,
        'volume': 42.4924120856802,
        'energy': -85125.8766752194,
        'energy_units': 'eV',
        'mulliken_charges': [0.363, 0.363, -0.363, -0.363],
        'mulliken_electrons': [27.637, 27.637, 8.363, 8.363],
        'mulliken_spin_total': 0.0,
        'mulliken_spins': [3.234, -3.234, -0.172, 0.172]
    }

    result_node = calc_node.get_outgoing().get_node_by_label('results')
    attributes = result_node.get_dict()
    attributes.pop('wall_time_seconds', None)
    assert set(attributes.keys()) == set(expected_results.keys())
    assert edict.diff(attributes, expected_results, np_allclose=True) == {}

    expected_struct = {
        'cell': [[0.0, -2.17339440672, -2.17339440672],
                 [0.0, -2.17339440672, 2.17339440672],
                 [-4.49784306967, 0.0, 0.0]],
        'kinds': [{'mass': 58.6934,
                   'name': 'Ni1',
                   'symbols': ['Ni'],
                   'weights': [1.0]},
                  {'mass': 58.6934,
                   'name': 'Ni2',
                   'symbols': ['Ni'],
                   'weights': [1.0]},
                  {'mass': 15.999,
                   'name': 'O',
                   'symbols': ['O'],
                   'weights': [1.0]}],
        'pbc1': True,
        'pbc2': True,
        'pbc3': True,
        'sites': [
            {'kind_name': 'Ni1',
             'position': [0.0, -2.17339440672, -2.17339440672]},
            {'kind_name': 'Ni2',
             'position': [-2.248921534835, -2.17339440672, 0.0]},
            {'kind_name': 'O',
             'position': [-2.248921534835, -2.17339440672, -2.17339440672]},
            {'kind_name': 'O', 'position': [0.0, -2.17339440672, 0.0]}]}

    outstruct_node = calc_node.get_outgoing().get_node_by_label('structure')

    assert edict.diff(outstruct_node.attributes,
                      expected_struct, np_allclose=True) == {}


@pytest.mark.skipif(os.environ.get("MOCK_CRY17_EXECUTABLES", True) != "true",
                    reason="the calculation was run on a HPC")
def test_run_nio_afm_failed_opt(db_test_app, get_structure, data_regression):
    # type: (AiidaTestApp) -> None
    """Test running a calculation where the optimisation fails,
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

    upload_basis_set_sto3g()

    # set up calculation
    process_class = code.get_builder().process_class
    builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data, code=code,
        metadata=db_test_app.get_default_metadata(),
        unflatten=True)

    outputs, calc_node = run_get_node(builder)
    # print(get_calcjob_report(calc_node))
    assert "optimisation" in outputs
    assert "results" in outputs

    calc_attributes = calc_node.attributes
    for key in ["job_id", "last_jobinfo", "remote_workdir",
                "scheduler_lastchecktime", "retrieve_singlefile_list"]:
        calc_attributes.pop(key, None)
    calc_attributes["retrieve_list"] = sorted(calc_attributes["retrieve_list"])

    data_regression.check({
        "calc_node": calc_attributes,
        "outputs": sorted(outputs.keys()),
        "results": outputs["results"].attributes,
        "optimisation": outputs["optimisation"].attributes
    })
