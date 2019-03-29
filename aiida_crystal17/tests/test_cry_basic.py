""" Tests for basic CRYSTAL17 calculation

"""
import os

import aiida_crystal17
from aiida_crystal17.tests import TEST_DIR
import ejplugins
from jsonextended import edict
import pytest


# @pytest.mark.skip(reason="awaiting fix for aiidateam/aiida_core#2650")
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
    builder.metadata.options.withmpi = False
    builder.metadata.options.resources = {
        "num_machines": 1, "num_mpiprocs_per_machine": 1}
    builder.input_file = infile

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = builder.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))


@pytest.mark.parametrize("inpath_main", (
    'mgo_sto3g_scf.crystal.d12',
    'mgo_sto3g_external.crystal.d12',
    'mgo_sto3g_opt.crystal.d12'
))
@pytest.mark.timeout(60)
@pytest.mark.process_execution
def test_run_runs(db_test_app, inpath_main):
    """Test running an optimisation calculation"""
    from aiida.engine import run_get_node
    from aiida.plugins import DataFactory
    SinglefileData = DataFactory('singlefile')

    code = db_test_app.get_or_create_code('crystal17.basic')

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files", inpath_main))

    # set up calculation
    builder = code.get_builder()
    builder.metadata = {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 30
        }
    }
    builder.input_file = infile

    outcome = run_get_node(builder)
    # result = outcome.result
    calc_node = outcome.node

    db_test_app.check_calculation(
        calc_node, ["results", "structure", "symmetry"])

    results = calc_node.get_outgoing().get_node_by_label('results')
    compare_expected_results(inpath_main, results)

    structure = calc_node.get_outgoing().get_node_by_label('structure')
    compare_expected_structure(inpath_main, structure)


def compare_expected_results(infile, result_node):
    if infile == "mgo_sto3g_scf.crystal.d12":
        expected = {
            'parser_version': str(aiida_crystal17.__version__),
            'ejplugins_version': str(ejplugins.__version__),
            'parser_class': 'CryMainParser',
            'parser_errors': [],
            'parser_warnings': ["no initial structure available, "
                                "creating new kinds for atoms"],
            'errors': [],
            'warnings': [],
            'energy': -2.7121814374931E+02 * 27.21138602,
            'energy_units': 'eV',  # hartree to eV
            'calculation_type':
            'restricted closed shell',
            'calculation_spin': False,
            # 'wall_time_seconds': 3,
            'number_of_atoms': 2,
            'number_of_assymetric': 2,
            'scf_iterations': 7,
            'volume': 18.65461527264623,
        }
    elif infile == "mgo_sto3g_external.crystal.d12":
        expected = {
            'parser_version': str(aiida_crystal17.__version__),
            'ejplugins_version': str(ejplugins.__version__),
            'parser_class': 'CryMainParser',
            'parser_errors': [],
            'parser_warnings': [
                "no initial structure available, "
                "creating new kinds for atoms"],
            'errors': [],
            'warnings': [],
            'energy': -2.7121814374931E+02 * 27.21138602,
            'energy_units': 'eV',  # hartree to eV
            'calculation_type': 'restricted closed shell',
            'calculation_spin': False,
            # 'wall_time_seconds': 3,
            'number_of_atoms': 2,
            'number_of_assymetric': 2,
            'scf_iterations': 7,
            'volume': 18.65461527264623,
            'mulliken_charges': [0.777, -0.777],
            'mulliken_electrons': [11.223, 8.777],
        }
    elif infile == "mgo_sto3g_opt.crystal.d12":
        expected = {
            'parser_version': str(aiida_crystal17.__version__),
            'ejplugins_version': str(ejplugins.__version__),
            'parser_class': 'CryMainParser',
            'parser_errors': [],
            'parser_warnings': ["no initial structure available, "
                                "creating new kinds for atoms"],
            'errors': [],
            'warnings': ['WARNING **** INT_SCREEN **** '
                         'CELL PARAMETERS OPTIMIZATION ONLY'],
            'energy': -2.712596206888E+02 * 27.21138602,
            'energy_units': 'eV',  # hartree to eV
            'calculation_type': 'restricted closed shell',
            'calculation_spin': False,
            # 'wall_time_seconds': 102,
            'number_of_atoms': 2,
            'number_of_assymetric': 2,
            'scf_iterations': 8,
            'opt_iterations': 6,
            'volume': 14.652065094424696,
        }
    else:
        raise ValueError()

    attributes = result_node.get_dict()
    attributes.pop('wall_time_seconds', None)
    assert set(attributes.keys()) == set(expected.keys())
    assert edict.diff(attributes, expected, np_allclose=True) == {}


def compare_expected_structure(infile, structure):
    if infile in ["mgo_sto3g_scf.crystal.d12",
                  "mgo_sto3g_external.crystal.d12"]:
        expected = {
            'cell': [[0.0, 2.105, 2.105],
                     [2.105, 0.0, 2.105],
                     [2.105, 2.105, 0.0]],
            'kinds': [
                {'mass': 24.305,
                 'name': 'Mg',
                 'symbols': ['Mg'],
                 'weights': [1.0]},
                {'mass': 15.9994,
                 'name': 'O',
                 'symbols': ['O'],
                 'weights': [1.0]}],
            'pbc1': True,
            'pbc2': True,
            'pbc3': True,
            'sites': [{'kind_name': 'Mg', 'position': [0.0, 0.0, 0.0]},
                      {'kind_name': 'O', 'position': [2.105, 2.105, 2.105]}]
        }
    elif infile == "mgo_sto3g_opt.crystal.d12":
        expected = {
            'cell': [[0.0, 1.94218061274, 1.94218061274],
                     [1.94218061274, 0.0, 1.94218061274],
                     [1.94218061274, 1.94218061274, 0.0]],
            'kinds': [
                {'mass': 24.305,
                 'name': 'Mg',
                 'symbols': ['Mg'],
                 'weights': [1.0]},
                {'mass': 15.9994,
                 'name': 'O',
                 'symbols': ['O'],
                 'weights': [1.0]}],
            'pbc1': True,
            'pbc2': True,
            'pbc3': True,
            'sites': [
                {'kind_name': 'Mg',
                 'position': [0.0, 0.0, 0.0]},
                {'kind_name': 'O',
                 'position': [1.94218061274, 1.94218061274, 1.94218061274]}]}
    else:
        raise ValueError()

    assert edict.diff(structure.attributes, expected, np_allclose=True) == {}


def compare_symmetry():
    expected_ops = [
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
    return expected_ops
