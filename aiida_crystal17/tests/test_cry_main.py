""" Tests for basic CRYSTAL17 calculation

"""
import os

import aiida_crystal17
import aiida_crystal17.tests as tests
import ejplugins
import numpy as np
import pytest
from jsonextended import edict

# TODO parameterize tests


def get_main_code(workdir):
    """get the crystal17.basic code """
    computer = tests.get_computer(workdir=workdir)
    # get code
    code = tests.get_code(entry_point='crystal17.main', computer=computer)

    return code


def test_submit(new_database, new_workdir):
    """Test submitting a calculation"""
    from aiida.orm import DataFactory
    SinglefileData = DataFactory('singlefile')
    StructureData = DataFactory('structure')
    from aiida.common.folders import SandboxFolder

    # get code
    code = get_main_code(new_workdir)

    # Prepare input parameters
    infile = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files",
                          'mgo_sto3g_external.crystal.d12'))
    instruct = StructureData()

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)
    calc.use_structure(instruct)

    calc.store_all()

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))
