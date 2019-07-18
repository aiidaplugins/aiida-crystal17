import os
from jsonextended import edict

from aiida.common.folders import SandboxFolder
from aiida.orm import RemoteData

from aiida_crystal17.immigration.create_inputs import populate_builder
from aiida_crystal17.immigration.create_calcjob import immigrate_existing
from aiida_crystal17.tests import TEST_FILES
from aiida_crystal17.tests.utils import get_default_metadata


def test_create_builder(db_test_app, data_regression):

    inpath = os.path.join(TEST_FILES, "crystal", "nio_sto3g_afm_scf", 'INPUT')
    outpath = os.path.join(TEST_FILES, "crystal", "nio_sto3g_afm_scf", 'main.out')

    with SandboxFolder() as folder:
        folder.insert_path(inpath, 'INPUT')
        folder.insert_path(outpath, 'main.out')

        remote = RemoteData(remote_path=folder.abspath,
                            computer=db_test_app.get_or_create_computer())

        builder = populate_builder(remote)

    assert set(builder["basissets"].keys()) == set(["Ni", "O"])

    data_regression.check(builder.parameters.attributes,
                          'test_create_builder_params')

    expected_settings = {
        'kinds': {
            'spin_alpha': ['Ni'],
            'spin_beta': ['Ni1'],
        },
        'operations':
        [[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
         [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
         [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
         [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
         [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
         [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
         [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
         [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
         [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
         [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
         [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
         [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
         [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
         [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
         [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
         [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]],
        'space_group':
        1,
        'crystal_type':
        1,
        'centring_code':
        1
    }

    assert builder.symmetry.compare_operations(
        expected_settings['operations']) == {}


def test_full_nio_afm(db_test_app, data_regression):

    inpath = os.path.join(TEST_FILES, "crystal", "nio_sto3g_afm_scf", 'INPUT')
    outpath = os.path.join(TEST_FILES, "crystal", "nio_sto3g_afm_scf", 'main.out')
    code = db_test_app.get_or_create_code('crystal17.main')

    metadata = get_default_metadata()
    metadata['options'].update({
        "input_file_name": 'other.d12',
        "output_main_file_name": "other2.out"
    })

    with SandboxFolder() as folder:
        folder.insert_path(inpath, 'other.d12')
        folder.insert_path(outpath, 'other2.out')

        remote = RemoteData(remote_path=folder.abspath,
                            computer=db_test_app.get_or_create_computer())

        builder = populate_builder(remote, code=code, metadata=metadata)

        node = immigrate_existing(builder, remote)

    attributes = node.attributes
    attributes["remote_workdir"] = "path/to/remote"
    attributes.pop("retrieve_singlefile_list", None)  # removed post v1.0.0b4

    data_regression.check(attributes)

    assert set(node.inputs) == set(
        ['basissets__Ni', 'basissets__O',
         'parameters', 'structure', 'symmetry', 'kinds', 'code'])

    assert set(node.outputs) == set(['results', 'remote_folder', 'retrieved'])


def test_full_mgo_opt(db_test_app, data_regression):

    inpath = os.path.join(TEST_FILES, "crystal", "mgo_sto3g_opt", 'INPUT')
    outpath = os.path.join(TEST_FILES, "crystal", "mgo_sto3g_opt", 'main.out')

    code = db_test_app.get_or_create_code('crystal17.main')

    with SandboxFolder() as folder:
        folder.insert_path(inpath, 'INPUT')
        folder.insert_path(outpath, 'main.out')

        remote = RemoteData(remote_path=folder.abspath,
                            computer=db_test_app.get_or_create_computer())

        builder = populate_builder(remote, code=code, metadata=get_default_metadata())

        node = immigrate_existing(builder, remote)

    attributes = node.attributes
    attributes["remote_workdir"] = "path/to/remote"
    attributes.pop("retrieve_singlefile_list", None)  # removed post v1.0.0b4

    data_regression.check(attributes)

    assert set(node.inputs) == set(
        ['basissets__Mg', 'basissets__O',
         'parameters', 'structure', 'symmetry', 'code'])

    assert set(node.outputs) == set(
        ['results', 'retrieved', 'structure', 'remote_folder'])

    expected_instruct_attrs = {
        'cell': [
            [0.0, 2.105, 2.105],
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

    assert edict.diff(
        dict(node.inputs.structure.attributes),
        expected_instruct_attrs, np_allclose=True, atol=1e-3) == {}

    expected_outstruct_attrs = {
        'cell': [
            [0.0, 1.94218061274, 1.94218061274],
            [1.94218061274, 0.0, 1.94218061274],
            [1.94218061274, 1.94218061274, 0.0]],
        'kinds': [
            {'mass': 24.305,
             'name': 'Mg',
             'symbols': ['Mg'],
             'weights': [1.0]},
            {'mass': 15.9994, 'name': 'O', 'symbols': ['O'], 'weights': [1.0]}],
        'pbc1': True,
        'pbc2': True,
        'pbc3': True,
        'sites': [
            {'kind_name': 'Mg',
             'position': [0.0, 0.0, 0.0]},
            {'kind_name': 'O',
             'position': [1.94218061274, 1.94218061274, 1.94218061274]}]
    }

    assert edict.diff(
        dict(node.outputs.structure.attributes),
        expected_outstruct_attrs, np_allclose=True, atol=1e-3) == {}
