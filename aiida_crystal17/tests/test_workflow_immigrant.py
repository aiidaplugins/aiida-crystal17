import os

from aiida_crystal17.tests import TEST_DIR
import pytest
from jsonextended import edict


@pytest.mark.timeout(30)
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


@pytest.mark.timeout(30)
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

    input_struct = node.inp.structure.get_pymatgen_structure().as_dict()
    # in later version of pymatgen only
    if "charge" in input_struct:
        input_struct.pop("charge")

    assert edict.diff(input_struct, expected_struct, np_allclose=True) == {}
