""" Tests for basic CRYSTAL17 calculation

"""
import os

import aiida_crystal17
import aiida_crystal17.tests.utils as tests
import ejplugins
import pytest
from aiida_crystal17.tests import TEST_DIR
from aiida_crystal17.aiida_compatability import aiida_version, cmp_version, run_get_node
from jsonextended import edict


def get_basic_code(workdir, configure=False):
    """get the crystal17.basic code """
    computer = tests.get_computer(workdir=workdir, configure=configure)
    code = tests.get_code(entry_point='crystal17.basic', computer=computer)

    return code


def test_submit(new_database, new_workdir):
    """Test submitting a calculation"""
    from aiida.orm.data.singlefile import SinglefileData
    from aiida.common.folders import SandboxFolder

    code = get_basic_code(new_workdir)

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files",
                          'mgo_sto3g_scf.crystal.d12'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)

    calc.store_all()

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))


@pytest.mark.process_execution
def test_process(new_database, new_workdir):
    """Test running a calculation
    note this does not test parsing of the output"""
    from aiida.orm.data.singlefile import SinglefileData

    # get code
    code = get_basic_code(new_workdir)

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files",
                          'mgo_sto3g_scf.crystal.d12'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)

    calc.store_all()

    # test process execution
    tests.test_calculation_execution(
        calc, check_paths=[calc._DEFAULT_OUTPUT_FILE])


@pytest.mark.process_execution
def test_process_with_external(new_database, new_workdir):
    """Test running a calculation
    note this does not test parsing of the output"""
    from aiida.orm.data.singlefile import SinglefileData

    # get code
    code = get_basic_code(new_workdir)

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files",
                          'mgo_sto3g_external.crystal.d12'))
    ingui = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files",
                          'mgo_sto3g_external.crystal.gui'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)
    calc.use_input_external(ingui)

    calc.store_all()

    # test process execution
    tests.test_calculation_execution(
        calc,
        check_paths=[calc._DEFAULT_OUTPUT_FILE, calc._DEFAULT_EXTERNAL_FILE])


def test_parser_scf(new_database, new_workdir):
    """ Test the parser

    """
    from aiida.parsers import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.orm import DataFactory

    code = get_basic_code(new_workdir)

    calc = code.new_calc()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("crystal17.basic")
    parser = parser_cls(calc)

    with SandboxFolder() as folder:
        main_out_path = os.path.join(
            os.path.dirname(tests.__file__), "output_files",
            "mgo_sto3g_scf.crystal.out")
        with open(main_out_path) as f:
            folder.create_file_from_filelike(f, "main.out")

        fdata = DataFactory("folder")()
        fdata.replace_with_folder(folder.abspath)

        mock_retrieved = {calc._get_linkname_retrieved(): fdata}
        success, node_list = parser.parse_with_retrieved(mock_retrieved)

    assert success

    node_dict = dict(node_list)
    assert set(['output_parameters', 'output_settings',
                'output_structure']) == set(node_dict.keys())

    expected_params = {
        'parser_version':
        str(aiida_crystal17.__version__),
        'ejplugins_version':
        str(ejplugins.__version__),
        'parser_class':
        'CryBasicParser',
        'parser_warnings':
        ["no initial structure available, creating new kinds for atoms"],
        'errors': [],
        'warnings': [],
        'energy': -2.7121814374931E+02 * 27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        # 'wall_time_seconds':
        # 3,
        'number_of_atoms':
        2,
        'number_of_assymetric':
        2,
        'scf_iterations':
        7,
        'volume':
        18.65461527264623,
    }

    out_params_dict = node_dict['output_parameters'].get_dict()
    # wall time is not fixed
    out_params_dict.pop('wall_time_seconds', None)

    assert edict.diff(
        node_dict['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}

    expected_struct_attrs = {
        'cell': [[0.0, 2.105, 2.105], [2.105, 0.0, 2.105], [2.105, 2.105, 0.0]],
        'kinds': [
            {'mass': 24.305,
             'name': 'Mg',
             'symbols': ['Mg'],
             'weights': [1.0]},
            {'mass': 15.9994, 'name': 'O', 'symbols': ['O'], 'weights': [1.0]}],
        'pbc1': True,
        'pbc2': True,
        'pbc3': True,
        'sites': [{'kind_name': 'Mg', 'position': [0.0, 0.0, 0.0]},
                  {'kind_name': 'O', 'position': [2.105, 2.105, 2.105]}]
    }

    assert edict.diff(
        dict(node_dict['output_structure'].get_attrs()),
        expected_struct_attrs, np_allclose=True) == {}


def test_parser_external(new_database, new_workdir):
    """ Test the parser

    """
    from aiida.parsers import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.orm import DataFactory

    code = get_basic_code(new_workdir)

    calc = code.new_calc()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("crystal17.basic")
    parser = parser_cls(calc)

    with SandboxFolder() as folder:
        main_out_path = os.path.join(
            os.path.dirname(tests.__file__), "output_files",
            "mgo_sto3g_external.crystal.out")
        with open(main_out_path) as f:
            folder.create_file_from_filelike(f, "main.out")

        fdata = DataFactory("folder")()
        fdata.replace_with_folder(folder.abspath)

        mock_retrieved = {calc._get_linkname_retrieved(): fdata}
        success, node_list = parser.parse_with_retrieved(mock_retrieved)

    assert success

    node_dict = dict(node_list)
    assert set(['output_parameters', 'output_settings',
                'output_structure']) == set(node_dict.keys())

    expected_params = {
        'parser_version':
        str(aiida_crystal17.__version__),
        'ejplugins_version':
        str(ejplugins.__version__),
        'parser_class':
        'CryBasicParser',
        'parser_warnings':
        ["no initial structure available, creating new kinds for atoms"],
        'errors': [],
        'warnings': [],
        'energy': -2.7121814374931E+02 *
        27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        # 'wall_time_seconds':
        # 3,
        'number_of_atoms':
        2,
        'number_of_assymetric':
        2,
        'scf_iterations':
        7,
        'volume':
        18.65461527264623,
        'mulliken_charges': [0.777, -0.777],
        'mulliken_electrons': [11.223, 8.777],
    }

    out_params_dict = node_dict['output_parameters'].get_dict()
    out_params_dict.pop('wall_time_seconds', None)

    assert edict.diff(
        out_params_dict,
        expected_params,
        np_allclose=True) == {}

    # read from nio_sto3g_afm.crystal.out
    expected_operations = [[
        1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
    ], [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0], [
        -1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0
    ], [1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0], [
        -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0], [
        0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
    ], [-1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], [
        0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0
    ], [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], [
        0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0
    ], [1.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 0.0, -1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0
    ], [1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0], [
        0.0, -1.0, 0.0, 1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], [
        1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0
    ], [-1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0], [
        -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0
    ], [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], [
        1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 0.0, -1.0, 1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, -1.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0
    ], [-1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0], [
        1.0, 1.0, 1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], [
        0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0
    ], [1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0], [
        0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
    ], [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0], [
        0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0
    ], [-1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [
        0.0, 0.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0
    ], [-1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0], [
        0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ], [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0], [
        -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
    ], [1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]]

    print(node_dict['output_settings'].data.operations)
    assert node_dict['output_settings'].compare_operations(
        expected_operations) == {}

    expected_struct_attrs = {
        'cell': [[0.0, 2.105, 2.105],
                 [2.105, 0.0, 2.105],
                 [2.105, 2.105, 0.0]],
        'kinds': [
            {'mass': 24.305,
             'name': 'Mg',
             'symbols': ['Mg'],
             'weights': [1.0]},
            {'mass': 15.9994, 'name': 'O',
             'symbols': ['O'], 'weights': [1.0]}],
        'pbc1': True,
        'pbc2': True,
        'pbc3': True,
        'sites': [{'kind_name': 'Mg', 'position': [0.0, 0.0, 0.0]},
                  {'kind_name': 'O', 'position': [2.105, 2.105, 2.105]}]
    }

    assert edict.diff(
        dict(node_dict['output_structure'].get_attrs()),
        expected_struct_attrs, np_allclose=True) == {}


def test_parser_opt(new_database, new_workdir):
    """ Test the parser

    """
    from aiida.parsers import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.orm import DataFactory

    code = get_basic_code(new_workdir)

    calc = code.new_calc()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("crystal17.basic")
    parser = parser_cls(calc)

    with SandboxFolder() as folder:
        main_out_path = os.path.join(
            os.path.dirname(tests.__file__), "output_files",
            "mgo_sto3g_opt.crystal.out")
        with open(main_out_path) as f:
            folder.create_file_from_filelike(f, "main.out")

        fdata = DataFactory("folder")()
        fdata.replace_with_folder(folder.abspath)

        mock_retrieved = {calc._get_linkname_retrieved(): fdata}
        success, node_list = parser.parse_with_retrieved(mock_retrieved)

    assert success

    node_dict = dict(node_list)
    assert set(['output_parameters', 'output_settings',
                'output_structure']) == set(node_dict.keys())

    expected_params = {
        'parser_version':
        str(aiida_crystal17.__version__),
        'ejplugins_version':
        str(ejplugins.__version__),
        'parser_class':
        'CryBasicParser',
        'parser_warnings':
        ["no initial structure available, creating new kinds for atoms"],
        'errors': [],
        'warnings':
        ['WARNING **** INT_SCREEN **** CELL PARAMETERS OPTIMIZATION ONLY'],
        'energy': -2.712596206888E+02 * 27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        # 'wall_time_seconds':
        # 102,
        'number_of_atoms':
        2,
        'number_of_assymetric':
        2,
        'scf_iterations':
        8,
        'opt_iterations':
        6,
        'volume':
        14.652065094424696,
    }

    out_params_dict = node_dict['output_parameters'].get_dict()
    out_params_dict.pop('wall_time_seconds', None)

    assert edict.diff(
        out_params_dict,
        expected_params,
        np_allclose=True) == {}

    expected_struct_attrs = {
        'cell': [[0.0, 1.94218061274, 1.94218061274],
                 [1.94218061274, 0.0, 1.94218061274],
                 [1.94218061274, 1.94218061274, 0.0]],
        'kinds': [{'mass': 24.305,
                   'name': 'Mg',
                   'symbols': [u'Mg'],
                   'weights': [1.0]},
                  {'mass': 15.9994, 'name': 'O', 'symbols': ['O'], 'weights': [1.0]}],
        'pbc1': True,
        'pbc2': True,
        'pbc3': True,
        'sites': [{'kind_name': 'Mg', 'position': [0.0, 0.0, 0.0]},
                  {'kind_name': 'O',
                   'position': [1.94218061274, 1.94218061274, 1.94218061274]}]
    }

    assert edict.diff(
        dict(node_dict['output_structure'].get_attrs()),
        expected_struct_attrs, np_allclose=True) == {}


@pytest.mark.timeout(60)
@pytest.mark.process_execution
@pytest.mark.skipif(
    aiida_version() < cmp_version('1.0.0a1') and tests.is_sqla_backend(),
    reason='Error in obtaining authinfo for computer configuration')
def test_full_run(new_database_with_daemon, new_workdir):
    """Test running a calculation"""
    from aiida.orm.data.singlefile import SinglefileData
    from aiida.common.datastructures import calc_states

    # get code
    code = get_basic_code(new_workdir, configure=True)

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files",
                          'mgo_sto3g_scf.crystal.d12'))

    # set up calculation
    calc = code.new_calc()

    inputs_dict = {
        "input_file": infile,
        "code": code,
        "options": {
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1
            },
            "withmpi": False,
            "max_wallclock_seconds": 30
        }
    }  # , "_use_cache": Bool(False)}

    process = calc.process()

    calcnode = run_get_node(process, inputs_dict)

    print(calcnode)

    assert '_aiida_cached_from' not in calcnode.extras()

    assert calcnode.get_state() == calc_states.FINISHED

    assert set(calcnode.get_outputs_dict().keys()).issuperset([
        'output_structure', 'output_parameters', 'output_settings', 'retrieved'
    ])

    expected_params = {
        'parser_version':
        str(aiida_crystal17.__version__),
        'ejplugins_version':
        str(ejplugins.__version__),
        'parser_class':
        'CryBasicParser',
        'parser_warnings':
        ["no initial structure available, creating new kinds for atoms"],
        'errors': [],
        'warnings': [],
        'energy': -2.7121814374931E+02 *
        27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        # 'wall_time_seconds':
        # 3,
        'number_of_atoms':
        2,
        'number_of_assymetric':
        2,
        'scf_iterations':
        7,
        'volume':
        18.65461527264623,
    }

    outputs = calcnode.get_outputs_dict()['output_parameters'].get_dict()
    # remove wall time, because it is run dependent
    outputs.pop('wall_time_seconds', None)

    assert edict.diff(
        outputs,
        expected_params,
        np_allclose=True) == {}
