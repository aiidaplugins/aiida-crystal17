import os

from aiida_crystal17.tests import TEST_DIR
import pytest


@pytest.mark.timeout(30)
def test_full(new_database):
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
        ['output_structure', 'output_parameters', 'retrieved'])

    assert '_aiida_cached_from' not in node.extras()

    # assert node.get_attr("state") == calc_states.FINISHED
