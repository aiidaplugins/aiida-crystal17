# -*- coding: utf-8 -*-
"""Submit a test calculation on localhost.

Usage: verdi run submit.py

Note: This script assumes you have set up computer and code as in README.md.
"""
import os

import aiida_crystal17.tests
import aiida_crystal17.tests as tests
import aiida_crystal17.tests.utils
import pytest


@pytest.mark.timeout(10)
def test_example(new_database, new_workdir):
    from aiida_crystal17.calculations.cry_main_immigrant import CryMainImmigrantCalculation

    # get code
    computer = aiida_crystal17.tests.utils.get_computer(
        workdir=new_workdir, configure=True)
    code = aiida_crystal17.tests.utils.get_code(
        entry_point='crystal17.main', computer=computer)

    resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 16}

    calc = CryMainImmigrantCalculation(
        computer=computer,
        resources=resources,
        remote_workdir=os.path.join(aiida_crystal17.tests.TEST_DIR,
                                    'immigrant_files'),
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

    print("Calculation migrated as pid: {}".format(calc.pk))


if __name__ == "__main__":

    wrkdir = "./aiida_workdir"
    if not os.path.exists(wrkdir):
        os.makedirs(wrkdir)

    test_example(None, os.path.abspath(wrkdir))
