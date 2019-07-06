""" Tests for basic CRYSTAL17 calculation

"""
import os

import ejplugins
from jsonextended import edict
import pytest

import aiida_crystal17
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import AiidaTestApp  # noqa: F401


def test_calcjob_submission(db_test_app):
    # type: (AiidaTestApp) -> None
    """Test submitting a calculation"""
    from aiida.plugins import DataFactory
    singlefile_data_cls = DataFactory('singlefile')

    # Prepare input parameters
    code = db_test_app.get_or_create_code('crystal17.basic')
    infile = singlefile_data_cls(
        file=os.path.join(TEST_FILES, "crystal", "mgo_sto3g_scf", 'INPUT'))
    infile.store()

    # set up calculation
    builder = code.get_builder()
    builder.metadata.options.withmpi = False
    builder.metadata.options.resources = {
        "num_machines": 1, "num_mpiprocs_per_machine": 1}
    builder.input_file = infile

    with db_test_app.sandbox_folder() as folder:
        calc_info = db_test_app.generate_calcinfo(
            'crystal17.basic', folder, builder)

        # Check the attributes of the returned `CalcInfo`
        assert calc_info.codes_info[0].cmdline_params == []
        assert sorted(calc_info.local_copy_list) == sorted(
            [[infile.uuid, infile.filename, u'INPUT']]
        )
        assert sorted(calc_info.retrieve_list) == sorted(['main.out', 'fort.34'])
        assert sorted(calc_info.retrieve_temporary_list) == sorted([])


@pytest.mark.parametrize("infolder,external_geom", (
    ('mgo_sto3g_scf', False),
    ('mgo_sto3g_opt', False),
    ('mgo_sto3g_scf_external', True)
))
@pytest.mark.process_execution
def test_calcjob_run(db_test_app, infolder, external_geom):
    # type: (AiidaTestApp, str, str) -> None
    """Test running an optimisation calculation"""
    from aiida.engine import run_get_node
    from aiida.plugins import DataFactory
    singlefile_data_cls = DataFactory('singlefile')

    code = db_test_app.get_or_create_code('crystal17.basic')

    # set up calculation
    builder = code.get_builder()
    builder.metadata = {
        "options": {
            "withmpi": False,
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 60
        }
    }
# .crystal.ingui # .crystal.d12
    # Prepare input parameters
    infile = singlefile_data_cls(
        file=os.path.join(TEST_FILES, "crystal", infolder, "INPUT"))
    builder.input_file = infile
    if external_geom:
        ingui = singlefile_data_cls(
            file=os.path.join(TEST_FILES, "crystal", infolder, "fort.34"))
        builder.input_external = ingui

    outcome = run_get_node(builder)
    # result = outcome.result
    calc_node = outcome.node

    db_test_app.check_calculation(
        calc_node, ["results", "structure", "symmetry"])

    results = calc_node.get_outgoing().get_node_by_label('results')
    compare_expected_results(infolder, results)

    structure = calc_node.get_outgoing().get_node_by_label('structure')
    compare_expected_structure(infolder, structure)


def compare_expected_results(infolder, result_node):
    if infolder == "mgo_sto3g_scf":
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
    elif infolder == "mgo_sto3g_scf_external":
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
    elif infolder == "mgo_sto3g_opt":
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
        raise ValueError(infolder)

    attributes = result_node.get_dict()
    attributes.pop('wall_time_seconds', None)
    assert set(attributes.keys()) == set(expected.keys())
    assert edict.diff(attributes, expected, np_allclose=True) == {}


def compare_expected_structure(infile, structure):
    if infile in ["mgo_sto3g_scf",
                  "mgo_sto3g_scf_external"]:
        expected = {
            'cell': [[0.0, 2.105, 2.105],
                     [2.105, 0.0, 2.105],
                     [2.105, 2.105, 0.0]],
            'kinds': [
                {'mass': 24.305,
                 'name': 'Mg',
                 'symbols': ['Mg'],
                 'weights': [1.0]},
                {'mass': 15.999,
                 'name': 'O',
                 'symbols': ['O'],
                 'weights': [1.0]}],
            'pbc1': True,
            'pbc2': True,
            'pbc3': True,
            'sites': [{'kind_name': 'Mg', 'position': [0.0, 0.0, 0.0]},
                      {'kind_name': 'O', 'position': [2.105, 2.105, 2.105]}]
        }
    elif infile == "mgo_sto3g_opt":
        expected = {
            'cell': [[0.0, 1.94218061274, 1.94218061274],
                     [1.94218061274, 0.0, 1.94218061274],
                     [1.94218061274, 1.94218061274, 0.0]],
            'kinds': [
                {'mass': 24.305,
                 'name': 'Mg',
                 'symbols': ['Mg'],
                 'weights': [1.0]},
                {'mass': 15.999,
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
