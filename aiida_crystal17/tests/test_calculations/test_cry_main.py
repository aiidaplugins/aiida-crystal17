""" Tests for main CRYSTAL17 calculation

"""
import os
from textwrap import dedent  # noqa: F401

import ejplugins
from jsonextended import edict
import pytest
from aiida.engine import run_get_node
from aiida.plugins import CalculationFactory, DataFactory, WorkflowFactory
import aiida_crystal17
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_create_builder(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    """test preparation of inputs"""
    db_test_app.get_or_create_code('crystal17.main')

    inparams = {"scf.k_points": (8, 8)}

    structure_data_cls = DataFactory('structure')
    basis_data_cls = DataFactory('crystal17.basisset')

    instruct = get_structure("MgO")
    mg_basis, _ = basis_data_cls.get_or_create(
        os.path.join(TEST_FILES, "basis_sets", "sto3g", 'sto3g_Mg.basis'))
    o_basis, _ = basis_data_cls.get_or_create(
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

    assert isinstance(builder.structure, structure_data_cls)
    builder.parameters


@pytest.mark.parametrize(
    "input_symmetry",
    (False, True)
)
def test_calcjob_submit_mgo(db_test_app, input_symmetry, get_structure):
    # type: (AiidaTestApp, bool) -> None
    """Test submitting a calculation"""

    param_data_cls = DataFactory('crystal17.parameters')
    basis_data_cls = DataFactory('crystal17.basisset')

    code = db_test_app.get_or_create_code('crystal17.main')

    # Prepare input parameters
    inparams = param_data_cls(data={
        "title": "MgO Bulk",
        "scf": {
            "k_points": (8, 8)
        }
    })

    instruct = get_structure("MgO")

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=DataFactory("dict")(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    mg_basis, _ = basis_data_cls.get_or_create(
        os.path.join(TEST_FILES, "basis_sets", "sto3g", 'sto3g_Mg.basis'))
    o_basis, _ = basis_data_cls.get_or_create(
        os.path.join(TEST_FILES, "basis_sets", "sto3g", 'sto3g_O.basis'))

    # set up calculation
    builder = code.get_builder()
    builder._update({"metadata": {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 30
        },
        "dry_run": True
    }})

    builder.parameters = inparams
    builder.structure = instruct
    builder.basissets = {"Mg": mg_basis, "O": o_basis}
    if input_symmetry:
        builder.symmetry = symmetry

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.main', folder, builder)

        cmdline_params = ['main']
        retrieve_list = ['main.out', 'main.gui']

        # Check the attributes of the returned `CalcInfo`
        assert calc_info.codes_info[0].cmdline_params == cmdline_params
        assert sorted(calc_info.local_copy_list) == sorted([])
        assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)
        assert sorted(calc_info.retrieve_temporary_list) == sorted([])

        assert sorted(folder.get_content_list()) == sorted([
            process_options.input_file_name, process_options.external_file_name
        ])

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()
        with folder.open(process_options.external_file_name) as f:
            gui_content = f.read()  # noqa: F841

    expected_input = dedent("""\
    MgO Bulk
    EXTERNAL
    END
    12 3
    1 0 3  2.  0.
    1 1 3  8.  0.
    1 1 3  2.  0.
    8 2
    1 0 3  2.  0.
    1 1 3  6.  0.
    99 0
    END
    SHRINK
    8 8
    END
    """)

    assert input_content == expected_input

    # TODO test .gui
    # assert gui_content == expected_gui


def test_calcjob_submit_nio_afm(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    """Test submitting a calculation"""

    kind_data_cls = DataFactory('crystal17.kinds')
    basis_data_cls = DataFactory('crystal17.basisset')
    upload_basisset_family = basis_data_cls.upload_basisset_family

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

    kind_data = kind_data_cls(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=DataFactory("dict")(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basisset_family(
        os.path.join(TEST_FILES, "basis_sets", "sto3g"),
        "sto3g",
        "minimal basis sets",
        stop_if_existing=True,
        extension=".basis")

    # set up calculation
    process_class = code.get_builder().process_class
    metadata = {
        "dry_run": True,
        "options": {
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1
            },
            "withmpi": False,
            "max_wallclock_seconds": 60,
        }}
    builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data,
        code=code, metadata=metadata, unflatten=True)

    process_options = builder.process_class(inputs=builder).metadata.options

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.main', folder, builder)

        cmdline_params = ['main']
        retrieve_list = ['main.out', 'main.gui']

        # Check the attributes of the returned `CalcInfo`
        assert calc_info.codes_info[0].cmdline_params == cmdline_params
        assert sorted(calc_info.local_copy_list) == sorted([])
        assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)
        assert sorted(calc_info.retrieve_temporary_list) == sorted([])

        assert sorted(folder.get_content_list()) == sorted([
            process_options.input_file_name, process_options.external_file_name
        ])

        with folder.open(process_options.input_file_name) as f:
            input_content = f.read()
        with folder.open(process_options.external_file_name) as f:
            gui_content = f.read()  # noqa: F841

    expected_input = dedent("""\
        NiO Bulk with AFM spin
        EXTERNAL
        END
        28 5
        1 0 3  2.  0.
        1 1 3  8.  0.
        1 1 3  8.  0.
        1 1 3  2.  0.
        1 3 3  8.  0.
        8 2
        1 0 3  2.  0.
        1 1 3  6.  0.
        99 0
        END
        UHF
        SHRINK
        8 8
        ATOMSPIN
        2
        1 1
        2 -1
        FMIXING
        30
        SPINLOCK
        0 15
        PPAN
        END
        """)

    assert input_content == expected_input

    # TODO test .gui
    # assert gui_content == expected_gui


def test_run_nio_afm_scf(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    """Test running a calculation"""

    kind_data_cls = DataFactory('crystal17.kinds')
    basisset_data_cls = DataFactory('crystal17.basisset')
    upload_basisset_family = basisset_data_cls.upload_basisset_family

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

    kind_data = kind_data_cls(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=DataFactory("dict")(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basisset_family(
        os.path.join(TEST_FILES, "basis_sets", "sto3g"),
        "sto3g",
        "minimal basis sets",
        stop_if_existing=True,
        extension=".basis")
    # basis_map = basis_data_cls.get_basis_group_map("sto3g")

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
def test_run_nio_afm_fullopt(db_test_app, get_structure):
    # type: (AiidaTestApp) -> None
    """Test running a calculation"""

    kind_data_cls = DataFactory('crystal17.kinds')
    basis_data_cls = DataFactory('crystal17.basisset')
    upload_basisset_family = basis_data_cls.upload_basisset_family

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

    kind_data = kind_data_cls(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=instruct,
        settings=DataFactory("dict")(dict={"symprec": 0.01, "compute_primitive": True})).node
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basisset_family(
        os.path.join(TEST_FILES, "basis_sets", "sto3g"),
        "sto3g",
        "minimal basis sets",
        stop_if_existing=True,
        extension=".basis")
    # basis_map = basis_data_cls.get_basis_group_map("sto3g")

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
