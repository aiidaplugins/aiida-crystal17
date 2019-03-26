import os
import shutil

from aiida_crystal17.tests import TEST_DIR


def test_full(db_test_app):
    from aiida_crystal17.calculations.cry_main_immigrant import (
        CryMainImmigrantCalculation)

    computer = db_test_app.get_or_create_computer()
    code = db_test_app.get_or_create_code('crystal17.main')

    inpath = os.path.join(TEST_DIR, "input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join(TEST_DIR, "output_files",
                           'nio_sto3g_afm.crystal.out')

    shutil.copy(inpath, db_test_app.work_directory)
    shutil.copy(outpath, db_test_app.work_directory)

    resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 16}

    calc = CryMainImmigrantCalculation(
        computer=computer,
        resources=resources,
        remote_workdir=db_test_app.work_directory,
        input_file_name='nio_sto3g_afm.crystal.d12',
        output_file_name='nio_sto3g_afm.crystal.out')
    calc.use_code(code)

    transport = computer.get_transport()

    with transport as open_transport:
        calc.create_input_nodes(open_transport)
        calc.prepare_for_retrieval_and_parsing(open_transport)

    assert set(calc.get_inputs_dict().keys()) == set(
        ['basis_O', 'parameters', 'settings', 'basis_Ni', 'code', 'structure'])

    # TODO block until parsed, then test outputs (requires workflow?)
    # print(calc.get_outputs_dict())
    # print(calc.has_finished())
    # print(calc.has_finished_ok())
    # print(calc.get_state())
    # print(calc.get_scheduler_error())
    # print(calc.get_scheduler_output())
    # from aiida.backends.utils import get_log_messages
    # print(get_log_messages(calc))
