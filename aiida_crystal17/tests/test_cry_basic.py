""" Tests for basic CRYSTAL17 calculation

"""
import os

import aiida_crystal17
import aiida_crystal17.tests as tests
import ejplugins
import pytest
from jsonextended import edict

# TODO parameterize tests


def get_basic_code(workdir):
    """get the crystal17.basic code """
    computer = tests.get_computer(workdir=workdir)
    # get code
    code = tests.get_code(entry_point='crystal17.basic', computer=computer)

    return code


def test_submit(new_database, new_workdir):
    """Test submitting a calculation"""
    from aiida.orm.data.singlefile import SinglefileData
    from aiida.common.folders import SandboxFolder

    # get code
    code = get_basic_code(new_workdir)

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files",
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
        file=os.path.join(tests.TEST_DIR, "input_files",
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
        file=os.path.join(tests.TEST_DIR, "input_files",
                          'mgo_sto3g_external.crystal.d12'))
    ingui = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files",
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
    assert set(['output_parameters',
                'output_structure']) == set(node_dict.keys())

    expected_params = {
        'parser_version': str(aiida_crystal17.__version__),
        'ejplugins_version': str(ejplugins.__version__),
        'parser_class': 'CryBasicParser',
        'parser_warnings': [],
        'errors': [],
        'warnings': [],
        'energy': -2.7121814374931E+02 * 27.21138602,
        'energy_units': 'eV',  # hartree to eV
        'calculation_type': 'restricted closed shell',
        'calculation_spin': False,
        'wall_time_seconds': 3,
        'number_of_atoms': 2,
        'number_of_assymetric': 2,
        'scf_iterations': 7,
        'volume': 18.65461527264623,
    }

    assert edict.diff(
        node_dict['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}

    expected_struct = {
        '@class':
        'Structure',
        '@module':
        'pymatgen.core.structure',
        'lattice': {
            'a':
            2.9769195487953652,
            'alpha':
            60.00000000000001,
            'b':
            2.9769195487953652,
            'beta':
            60.00000000000001,
            'c':
            2.9769195487953652,
            'gamma':
            60.00000000000001,
            'matrix': [[0.0, 2.105, 2.105], [2.105, 0.0, 2.105],
                       [2.105, 2.105, 0.0]],
            'volume':
            18.65461525
        },
        'sites': [{
            'abc': [0.0, 0.0, 0.0],
            'label': 'Mg',
            'species': [{
                'element': 'Mg',
                'occu': 1.0
            }],
            'xyz': [0.0, 0.0, 0.0]
        }, {
            'abc': [0.5, 0.5, 0.5],
            'label': 'O',
            'species': [{
                'element': 'O',
                'occu': 1.0
            }],
            'xyz': [2.105, 2.105, 2.105]
        }]
    }

    output_struct = node_dict[
        'output_structure'].get_pymatgen_structure().as_dict()
    # in later version of pymatgen only
    if "charge" in output_struct:
        output_struct.pop("charge")

    assert edict.diff(output_struct, expected_struct, np_allclose=True) == {}


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
    assert set(['output_parameters',
                'output_structure']) == set(node_dict.keys())

    expected_params = {
        'parser_version': str(aiida_crystal17.__version__),
        'ejplugins_version': str(ejplugins.__version__),
        'parser_class': 'CryBasicParser',
        'parser_warnings': [],
        'errors': [],
        'warnings': [],
        'energy': -2.7121814374931E+02 * 27.21138602,
        'energy_units': 'eV',  # hartree to eV
        'calculation_type': 'restricted closed shell',
        'calculation_spin': False,
        'wall_time_seconds': 3,
        'number_of_atoms': 2,
        'number_of_assymetric': 2,
        'scf_iterations': 7,
        'volume': 18.65461527264623,
        'mulliken_electrons': [11.223, 8.777],
        'mulliken_charges': [0.777, -0.777]
    }

    assert edict.diff(
        node_dict['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}

    expected_struct = {
        '@class':
        'Structure',
        '@module':
        'pymatgen.core.structure',
        'lattice': {
            'a':
            2.9769195487953652,
            'alpha':
            60.00000000000001,
            'b':
            2.9769195487953652,
            'beta':
            60.00000000000001,
            'c':
            2.9769195487953652,
            'gamma':
            60.00000000000001,
            'matrix': [[0.0, 2.105, 2.105], [2.105, 0.0, 2.105],
                       [2.105, 2.105, 0.0]],
            'volume':
            18.65461525
        },
        'sites': [{
            'abc': [0.0, 0.0, 0.0],
            'label': 'Mg',
            'species': [{
                'element': 'Mg',
                'occu': 1.0
            }],
            'xyz': [0.0, 0.0, 0.0]
        }, {
            'abc': [0.5, 0.5, 0.5],
            'label': 'O',
            'species': [{
                'element': 'O',
                'occu': 1.0
            }],
            'xyz': [2.105, 2.105, 2.105]
        }]
    }

    output_struct = node_dict[
        'output_structure'].get_pymatgen_structure().as_dict()
    # in later version of pymatgen only
    if "charge" in output_struct:
        output_struct.pop("charge")

    assert edict.diff(output_struct, expected_struct, np_allclose=True) == {}


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
    assert set(['output_parameters',
                'output_structure']) == set(node_dict.keys())

    expected_params = {
        'parser_version':
        str(aiida_crystal17.__version__),
        'ejplugins_version':
        str(ejplugins.__version__),
        'parser_class':
        'CryBasicParser',
        'parser_warnings': [],
        'errors': [],
        'warnings':
        ['WARNING **** INT_SCREEN **** CELL PARAMETERS OPTIMIZATION ONLY'],
        'energy':
        -2.712596206888E+02 * 27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        'wall_time_seconds':
        102,
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

    assert edict.diff(
        node_dict['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}

    expected_struct = {
        '@class':
        'Structure',
        '@module':
        'pymatgen.core.structure',
        'lattice': {
            'a':
            2.746658163114996,
            'alpha':
            60.00000000000001,
            'b':
            2.746658163114996,
            'beta':
            60.00000000000001,
            'c':
            2.746658163114996,
            'gamma':
            60.00000000000001,
            'matrix': [[0.0, 1.94218061274,
                        1.94218061274], [1.94218061274, 0.0, 1.94218061274],
                       [1.94218061274, 1.94218061274, 0.0]],
            'volume':
            14.652065094424696
        },
        'sites': [{
            'abc': [0.0, 0.0, 0.0],
            'label': 'Mg',
            'species': [{
                'element': 'Mg',
                'occu': 1.0
            }],
            'xyz': [0.0, 0.0, 0.0]
        }, {
            'abc': [0.5, 0.5, 0.5],
            'label': 'O',
            'species': [{
                'element': 'O',
                'occu': 1.0
            }],
            'xyz': [1.942180612737, 1.942180612737, 1.942180612737]
        }]
    }

    output_struct = node_dict[
        'output_structure'].get_pymatgen_structure().as_dict()
    # in later version of pymatgen only
    if "charge" in output_struct:
        output_struct.pop("charge")

    assert edict.diff(output_struct, expected_struct, np_allclose=True) == {}


# TODO test that the calculation completed successfully (the code below doesn't work)

# def test_output(test_data):
#     """Test submitting a calculation"""
#     from aiida.orm.data.singlefile import SinglefileData
#     try:
#         from aiida.work.run import submit, run
#     except ImportError:
#         from aiida.work.launch import submit, run
#
#     code = tests.get_code(
#         entry_point='crystal17.basic')
#
#     infile = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'mgo_sto3g.d12'))
#
#     # set up calculation
#     calc = code.new_calc()
#     # calc.label = "aiida_crystal17 test"
#     # calc.description = "Test job submission with the aiida_crystal17 plugin"
#     # calc.set_max_wallclock_seconds(30)
#     # calc.set_withmpi(False)
#     # calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
#     #
#     # calc.use_input_file(infile)
#
#     # calc.store_all()
#
#     inputs = {"_options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
#                           "withmpi": False, "max_wallclock_seconds": False},
#               "_label": "aiida_crystal17 test",
#               "_description": "Test job submission with the aiida_crystal17 plugin",
#               "input_file": infile,
#               "code": code}
#
#     print("running")
#     run(calc.__class__.process(), **inputs)
#     # print("submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
#     #     calc.uuid, calc.dbnode.pk))

# def test_output2(test_data):
#     """Test calculation output"""
#     from aiida.orm.data.singlefile import SinglefileData
#     from aiida.work.workchain import WorkChain, ToContext, append_
#     from aiida.orm.utils import CalculationFactory
#     from aiida.common.exceptions import MissingPluginError
#     from aiida_quantumespresso.utils.mapping import prepare_process_inputs
#
#     try:
#         from aiida.work.run import submit
#     except ImportError:
#         from aiida.work.launch import submit
#
#     class RetrieveOutput(WorkChain):
#
#         @classmethod
#         def define(cls, spec):
#             super(RetrieveOutput, cls).define(spec)
#             spec.input('infile')
#             spec.outline(
#                 cls.submit_calc,
#                 cls.inspect_calc
#             )
#
#         def submit_calc(self):
#             # set up calculation
#
#             code = tests.get_code(
#                 entry_point='crystal17.basic')
#             calc = code.new_calc()  # type: CryBasicCalculation
#
#             # plugin_name = code.get_input_plugin_name()
#             # if plugin_name is None:
#             #     raise ValueError("You did not specify an input plugin "
#             #                      "for this code")
#             # try:
#             #     calc_cls = CalculationFactory(plugin_name)
#             #
#             # except MissingPluginError:
#             #     raise MissingPluginError("The input_plugin name for this code is "
#             #                              "'{}', but it is not an existing plugin"
#             #                              "name".format(plugin_name))
#
#
#             calc.label = "aiida_crystal17 test"
#             calc.description = "Test job submission with the aiida_crystal17 plugin"
#             calc.set_max_wallclock_seconds(30)
#             calc.set_withmpi(False)
#             calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
#             calc.use_input_file(infile)
#
#             # calc.store_all()
#             #
#             # inputs = prepare_process_inputs({"_options": {"resources": None}})
#             # inputs._options.resources = {"num_machines": 1, "num_mpiprocs_per_machine": 1}
#             #
#             # print(inputs)
#
#
#             # calc_inputs = {
#             #     "max_wallclock_seconds": 30,
#             #     "withmpi": False,
#             #     "jobresource_params": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
#             # }
#             #
#             # calc_inputs = prepare_process_inputs(calc_inputs)
#
#             print(list(calc.attrs()))
#
#             # future = submit(calc.process(), inputs)
#             print(calc.process().spec().get_inputs_template())
#             inputs = {"_options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
#                                   "withmpi": False, "max_wallclock_seconds": False},
#                       "_label": "aiida_crystal17 test",
#                       "_description": "Test job submission with the aiida_crystal17 plugin",
#                       # "input_file": infile,
#                       "code": code}
#
#             future = submit(calc.process(), **inputs)
#
#             return ToContext(calculation=append_(future))
#
#             # return self.to_context(calculation=future)
#
#         def inspect_calc(self):
#             assert self.ctx.calculation.is_finished_ok
#
#     infile = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'mgo_sto3g.d12'))
#
#     RetrieveOutput.run(infile=infile)
#
#
#
#
#
