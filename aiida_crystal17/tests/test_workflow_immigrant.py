import os
import aiida_crystal17.tests as tests
import pytest


@pytest.mark.timeout(30)
def test_full(new_database):
    from aiida_crystal17.workflows.cry_main_immigrant import migrate_as_main
    from aiida.common.datastructures import calc_states

    inpath = os.path.join(tests.TEST_DIR, "input_files",
                          'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join(tests.TEST_DIR, "output_files",
                           'nio_sto3g_afm.crystal.out')

    node = migrate_as_main(inpath, outpath)

    print(list(node.attrs()))

    assert node.is_stored

    assert set(node.get_inputs_dict().keys()) == set(
        ['basis_Ni', 'basis_O', 'parameters', 'structure', 'settings'])

    assert set(node.get_outputs_dict().keys()).issuperset(
        ['output_structure', 'output_parameters', 'output_arrays'])

    # assert node.get_attr("state") == calc_states.FINISHED
