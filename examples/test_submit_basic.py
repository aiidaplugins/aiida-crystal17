# -*- coding: utf-8 -*-
"""Submit a test calculation on localhost.

Usage: verdi run submit.py

Note: This script assumes you have set up computer and code as in README.md.
"""
import os
import aiida_crystal17.tests as tests


def get_basic_code(workdir):
    """get the crystal17.basic code """
    computer = tests.get_computer(workdir=workdir)
    # get code
    code = tests.get_code(entry_point='crystal17.basic', computer=computer)

    return code


def test_example(new_database, new_workdir):

    from aiida.orm import DataFactory
    # try:
    #     from aiida.work import submit  # for aiida<1.0
    # except ImportError:
    #     from aiida.work.launch import submit  # for aiida>=1.0

    # get code
    code = get_basic_code(new_workdir)

    # Prepare input parameters
    SinglefileData = DataFactory("singlefile")
    # main .d12 file
    infile = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files",
                          'mgo_sto3g_external.crystal.d12'))
    # optional .gui file (for use with EXTERNAL)
    ingeom = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files",
                          'mgo_sto3g_external.crystal.gui'))

    # set up calculation
    calc = code.new_calc()
    calc.label = "aiida_crystal17 test"
    calc.description = "Test job submission with the aiida_crystal17 plugin"
    calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)
    calc.use_input_external(ingeom)

    calc.store_all()

    calc.submit()  # TODO this hangs when using aiida develop branch on travis

    print("submitted calculation; calc=Calculation(PK={})".format(
        calc.dbnode.pk))


if __name__ == "__main__":

    wrkdir = "./aiida_workdir"
    if not os.path.exists(wrkdir):
        os.makedirs(wrkdir)

    test_example(None, os.path.abspath(wrkdir))
