""" Tests for basic CRYSTAL17 calculation

"""
import os

import aiida_crystal17
import ejplugins
import pytest
from aiida_crystal17.tests import TEST_DIR
from jsonextended import edict


def test_submit(db_test_app):
    """Test submitting a calculation"""
    from aiida.plugins import DataFactory
    SinglefileData = DataFactory('singlefile')

    from aiida.common.folders import SandboxFolder

    code = db_test_app.get_or_create_code('crystal17.basic')

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files",
                          'mgo_sto3g_scf.crystal.d12'))

    # set up calculation
    builder = code.get_builder()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    builder.metadata.options.withmpi = False
    builder.metadata.options.resources = {
        "num_machines": 1, "num_mpiprocs_per_machine": 1}
    builder.input_file = infile

    # calc.store_all()

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = builder.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))


def test_parser_scf(db_test_app):
    """ Test the parser

    """
    from aiida.plugins import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.plugins import DataFactory

    code = db_test_app.get_or_create_code('crystal17.basic')

    calc = code.get_builder()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("crystal17.basic")
    parser = parser_cls(calc)

    with SandboxFolder() as folder:
        main_out_path = os.path.join(
            TEST_DIR, "output_files",
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
        'energy':
        -2.7121814374931E+02 * 27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        'wall_time_seconds':
        3,
        'number_of_atoms':
        2,
        'number_of_assymetric':
        2,
        'scf_iterations':
        7,
        'volume':
        18.65461527264623,
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
        },
            {
            'abc': [0.5, 0.5, 0.5],
            'label': 'O',
            'species': [{
                'element': 'O',
                'occu': 1.0
            }],
            'xyz': [2.105, 2.105, 2.105]
        }]
    }

    output_struct = node_dict['output_structure'].get_pymatgen_structure(
    ).as_dict()
    # in later version of pymatgen only
    if "charge" in output_struct:
        output_struct.pop("charge")

    assert edict.diff(output_struct, expected_struct, np_allclose=True) == {}


def test_parser_external(db_test_app):
    """ Test the parser

    """
    from aiida.plugins import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.plugins import DataFactory

    code = db_test_app.get_or_create_code('crystal17.basic')

    calc = code.get_builder()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("crystal17.basic")
    parser = parser_cls(calc)

    with SandboxFolder() as folder:
        main_out_path = os.path.join(
            TEST_DIR, "output_files",
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
        'energy':
        -2.7121814374931E+02 * 27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        'wall_time_seconds':
        3,
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

    assert edict.diff(
        node_dict['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}

    # read from nio_sto3g_afm.crystal.out
    expected_operations = [
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, -1.0, -1.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, -1.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    ]

    print(node_dict['output_settings'].data.operations)
    assert node_dict['output_settings'].compare_operations(
        expected_operations) == {}

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
        },
            {
            'abc': [0.5, 0.5, 0.5],
            'label': 'O',
            'species': [{
                'element': 'O',
                'occu': 1.0
            }],
            'xyz': [2.105, 2.105, 2.105]
        }]
    }

    output_struct = node_dict['output_structure'].get_pymatgen_structure(
    ).as_dict()
    # in later version of pymatgen only
    if "charge" in output_struct:
        output_struct.pop("charge")

    assert edict.diff(output_struct, expected_struct, np_allclose=True) == {}


def test_parser_opt(db_test_app):
    """ Test the parser

    """
    from aiida.parsers import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.plugins import DataFactory

    code = db_test_app.get_or_create_code('crystal17.basic')

    calc = code.get_builder()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("crystal17.basic")
    parser = parser_cls(calc)

    with SandboxFolder() as folder:
        main_out_path = os.path.join(
            TEST_DIR, "output_files",
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
            'matrix': [[0.0, 1.94218061274, 1.94218061274],
                       [1.94218061274, 0.0, 1.94218061274],
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
        },
            {
            'abc': [0.5, 0.5, 0.5],
            'label': 'O',
            'species': [{
                'element': 'O',
                'occu': 1.0
            }],
            'xyz': [1.942180612737, 1.942180612737, 1.942180612737]
        }]
    }

    output_struct = node_dict['output_structure'].get_pymatgen_structure(
    ).as_dict()
    # in later version of pymatgen only
    if "charge" in output_struct:
        output_struct.pop("charge")

    assert edict.diff(output_struct, expected_struct, np_allclose=True) == {}


@pytest.mark.timeout(60)
@pytest.mark.process_execution
def test_full_run(db_test_app):
    """Test running a calculation"""
    from aiida.engine import run_get_node
    from aiida.plugins import DataFactory
    SinglefileData = DataFactory('singlefile')

    code = db_test_app.get_or_create_code('crystal17.basic')

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files",
                              'mgo_sto3g_scf.crystal.d12'))

    # set up calculation
    calc = code.get_builder()

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

    if not calcnode.get_state() == "FINISHED":
        error_msg = "calc state not FINISHED: {}".format(calcnode.get_state())
        if 'output_parameters' in calcnode.get_outputs_dict():
            error_msg += "\n{}".format(
                calcnode.get_outputs_dict()['output_parameters'].get_dict())
        raise AssertionError(error_msg)

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
        'energy':
        -2.7121814374931E+02 * 27.21138602,
        'energy_units':
        'eV',  # hartree to eV
        'calculation_type':
        'restricted closed shell',
        'calculation_spin':
        False,
        'wall_time_seconds':
        3,
        'number_of_atoms':
        2,
        'number_of_assymetric':
        2,
        'scf_iterations':
        7,
        'volume':
        18.65461527264623,
    }

    assert edict.diff(
        calcnode.get_outputs_dict()['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}
