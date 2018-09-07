import os
import shutil
import pytest
import aiida_crystal17.tests as tests


def get_main_code(workdir):
    """get the crystal17.basic code """
    computer = tests.get_computer(workdir=workdir)
    # get code
    code = tests.get_code(entry_point='crystal17.main', computer=computer)

    return code


@pytest.mark.master_sqlalchemy_fail
def test_full(new_database, new_workdir):
    from aiida_crystal17.calculations.cry_main_immigrant import CryMainImmigrantCalculation

    computer = tests.get_computer(workdir=new_workdir, configure=True)
    code = tests.get_code(entry_point='crystal17.main', computer=computer)

    inpath = os.path.join(tests.TEST_DIR, "input_files",
                          'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join(tests.TEST_DIR, "output_files",
                           'nio_sto3g_afm.crystal.out')

    shutil.copy(inpath, new_workdir)
    shutil.copy(outpath, new_workdir)

    resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 16}

    calc = CryMainImmigrantCalculation(
        computer=computer,
        resources=resources,
        remote_workdir=new_workdir,
        input_file_name='nio_sto3g_afm.crystal.d12',
        output_file_name='nio_sto3g_afm.crystal.out')
    calc.use_code(code)

    try:
        # aiida v0.12
        from aiida.backends.utils import get_authinfo, get_automatic_user
        authinfo = get_authinfo(
            computer=computer, aiidauser=get_automatic_user())
        transport = authinfo.get_transport()
    except ImportError:
        # aiida v1
        transport = computer.get_transport()

    with transport as open_transport:
        calc.create_input_nodes(open_transport)
        calc.prepare_for_retrieval_and_parsing(open_transport)

    assert set(calc.get_inputs_dict().keys()) == set(['basis_O', 'parameters', 'settings',
                                                      'basis_Ni', 'code', 'structure'])

    # TODO block until parsed, then test outputs (requires workflow?)
    # print(calc.get_outputs_dict())
    # print(calc.has_finished())
    # print(calc.has_finished_ok())
    # print(calc.get_state())
    # print(calc.get_scheduler_error())
    # print(calc.get_scheduler_output())
    # from aiida.backends.utils import get_log_messages
    # print(get_log_messages(calc))

