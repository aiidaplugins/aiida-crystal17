# -*- coding: utf-8 -*-
"""Submit a test calculation on localhost.

Usage: verdi run submit.py

Note: This script assumes you have set up computer and code as in README.md.
"""
import os
import aiida_crystal17.tests as tests
import pytest


@pytest.mark.develop_fail
def test_example(new_database, new_workdir):
    # get code
    # computer = tests.get_computer(workdir=new_workdir, configure=True)
    # code = tests.get_code(entry_point='crystal17.main', computer=computer)
    from aiida.orm import Code, Computer
    computer = Computer.get('local')
    code = Code.get_from_string('immigrant')

    resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 16}

    from aiida_quantumespresso.calculations.pwimmigrant import PwimmigrantCalculation
    calc = PwimmigrantCalculation(
        computer=computer,
        resources=resources,
        remote_workdir=
        'GitHub/aiida-crystal17/examples/pwimmigrant',  # os.path.join(tests.TEST_DIR, 'pwimmigrant_files'),
        input_file_name='iron_sulfide_2fetypes.main.in',
        output_file_name='iron_sulfide.vc-relax.qe.out')
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
