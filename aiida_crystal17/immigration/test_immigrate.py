import os
from jsonextended import edict

from aiida_crystal17.immigration.create_inputs import populate_builder
from aiida_crystal17.tests import TEST_DIR


def test_create_builder(db_test_app):
    from aiida.orm import FolderData
    inpath = os.path.join(TEST_DIR, "input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join(TEST_DIR, "output_files",
                           'nio_sto3g_afm.crystal.out')

    folder = FolderData()
    folder.put_object_from_file(inpath, "main.d12")
    folder.put_object_from_file(outpath, "main.out")

    builder = populate_builder(
        folder, input_name="main.d12", output_name="main.out")

    assert set(builder["basissets"].keys()) == set(["Ni", "O"])

    expected_params = {
        'scf': {
            'single': 'UHF',
            'numerical': {
                'FMIXING': 30
            },
            'post_scf': ['PPAN'],
            'spinlock': {
                'SPINLOCK': [0, 15]
            },
            'k_points': [8, 8]
        },
        'title': 'NiO Bulk with AFM spin'
    }

    assert builder.parameters.get_dict() == expected_params

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


def test_full_nio_afm(db_test_app):
    from aiida.plugins import DataFactory
    from aiida_crystal17.immigration.cry_main import migrate_as_main

    inpath = os.path.join(TEST_DIR, "input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join(TEST_DIR, "output_files",
                           'nio_sto3g_afm.crystal.out')
    folder = DataFactory('folder')()
    folder.put_object_from_file(inpath, "main.d12")
    folder.put_object_from_file(outpath, "main.out")

    node = migrate_as_main(
        folder,
        db_test_app.get_or_create_code('crystal17.main'),
        store_all=True
    )

    print(node.inputs)

    assert set(node.inputs) == set(
        ['basissets__Ni', 'basissets__O',
         'parameters', 'structure', 'symmetry', 'kinds', 'code'])

    node.inputs.structure

    print(node.outputs)

    assert set(node.outputs) == set(
        ['results', 'retrieved'])

    # assert node.get_attribute("state") == calc_states.FINISHED


def test_full_mgo_opt(db_test_app):
    from aiida.plugins import DataFactory
    from aiida_crystal17.immigration.cry_main import migrate_as_main

    inpath = os.path.join(TEST_DIR, "input_files", 'mgo_sto3g_opt.crystal.d12')
    outpath = os.path.join(TEST_DIR, "output_files",
                           'mgo_sto3g_opt.crystal.out')
    folder = DataFactory('folder')()
    folder.put_object_from_file(inpath, "main.d12")
    folder.put_object_from_file(outpath, "main.out")

    node = migrate_as_main(
        folder,
        db_test_app.get_or_create_code('crystal17.main'),
        store_all=True
    )

    print(node.inputs)

    assert set(node.inputs) == set(
        ['basissets__Mg', 'basissets__O',
         'parameters', 'structure', 'symmetry', 'code'])

    node.inputs.structure

    print(node.outputs)

    assert set(node.outputs) == set(
        ['results', 'retrieved', 'structure'])

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
