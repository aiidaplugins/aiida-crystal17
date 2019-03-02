import os

from aiida_crystal17.tests import TEST_DIR
import pytest
from jsonextended import edict


@pytest.mark.timeout(60)
def test_full_nio_afm(new_database):
    from aiida.orm import DataFactory
    from aiida_crystal17.workflows.cry_main_immigrant import migrate_as_main
    # from aiida.common.datastructures import calc_states

    work_dir = TEST_DIR
    inpath = os.path.join("input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join("output_files", 'nio_sto3g_afm.crystal.out')

    node = migrate_as_main(
        work_dir,
        inpath,
        outpath,
        input_links={
            'structure': {
                "struct_setup": DataFactory('parameter')()
            }
        })

    print(list(node.attrs()))

    assert node.is_stored

    assert set(node.get_inputs_dict().keys()) == set(
        ['basis_Ni', 'basis_O', 'parameters', 'structure', 'settings'])

    struct = node.inp.structure
    assert "struct_setup" in struct.get_inputs_dict()[
        'structure'].get_inputs_dict()

    print(node.get_outputs_dict())

    assert set(node.get_outputs_dict().keys()).issuperset(
        ['output_parameters', 'retrieved'])

    assert '_aiida_cached_from' not in node.extras()

    # assert node.get_attr("state") == calc_states.FINISHED


@pytest.mark.timeout(60)
def test_full_mgo_opt(new_database):
    from aiida.orm import DataFactory
    from aiida_crystal17.workflows.cry_main_immigrant import migrate_as_main
    # from aiida.common.datastructures import calc_states

    work_dir = TEST_DIR
    inpath = os.path.join("input_files", 'mgo_sto3g_opt.crystal.d12')
    outpath = os.path.join("output_files", 'mgo_sto3g_opt.crystal.out')

    node = migrate_as_main(
        work_dir,
        inpath,
        outpath,
        input_links={
            'structure': {
                "struct_setup": DataFactory('parameter')()
            }
        })

    print(list(node.attrs()))

    assert node.is_stored

    assert set(node.get_inputs_dict().keys()) == set(
        ['basis_Mg', 'basis_O', 'parameters', 'structure', 'settings'])

    struct = node.inp.structure
    assert "struct_setup" in struct.get_inputs_dict()[
        'structure'].get_inputs_dict()

    print(node.get_outputs_dict())

    assert set(node.get_outputs_dict().keys()).issuperset(
        ['output_parameters', 'output_structure', 'retrieved'])

    assert '_aiida_cached_from' not in node.extras()

    # assert node.get_attr("state") == calc_states.FINISHED

    expected_struct_attrs = {
        'cell': [
            [0.0, 2.105, 2.105],
            [2.105, 0.0, 2.105],
            [2.105, 2.105, 0.0]],
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
        dict(node.get_outputs_dict()['output_structure'].get_attrs()),
        expected_struct_attrs, np_allclose=True) == {}
