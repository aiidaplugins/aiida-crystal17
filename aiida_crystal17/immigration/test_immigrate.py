import os
from jsonextended import edict

from aiida_crystal17.immigration.create_inputs import populate_builder
from aiida_crystal17.immigration.create_calcjob import create_crymain
from aiida_crystal17.tests import TEST_DIR
from aiida_crystal17.tests.utils import get_default_metadata


def test_create_builder(db_test_app, data_regression):

    inpath = os.path.join("input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join("output_files",
                           'nio_sto3g_afm.crystal.out')

    builder = populate_builder(
        TEST_DIR, input_name=inpath, output_name=outpath)

    assert set(builder["basissets"].keys()) == set(["Ni", "O"])

    data_regression.check(builder.parameters.attributes, 'test_create_builder_params')

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

    inpath = os.path.join("input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join("output_files",
                           'nio_sto3g_afm.crystal.out')
    code = db_test_app.get_or_create_code('crystal17.main')

    builder = populate_builder(TEST_DIR, inpath, outpath, code=code, metadata=get_default_metadata())
    node = create_crymain(builder, TEST_DIR, outpath)

    data_regression.check(node.attributes)

    assert set(node.inputs) == set(
        ['basissets__Ni', 'basissets__O',
         'parameters', 'structure', 'symmetry', 'kinds', 'code'])

    assert set(node.outputs) == set(
        ['results', 'retrieved'])


def test_full_mgo_opt(db_test_app, data_regression):

    inpath = os.path.join("input_files", 'mgo_sto3g_opt.crystal.d12')
    outpath = os.path.join("output_files",
                           'mgo_sto3g_opt.crystal.out')

    builder = populate_builder(
        TEST_DIR, inpath, outpath,
        db_test_app.get_or_create_code('crystal17.main'),
        get_default_metadata()
    )
    node = create_crymain(builder, TEST_DIR, outpath)

    data_regression.check(node.attributes)

    assert set(node.inputs) == set(
        ['basissets__Mg', 'basissets__O',
         'parameters', 'structure', 'symmetry', 'code'])

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
