""" Tests for basic CRYSTAL17 calculation

"""
import glob
import os

import aiida_crystal17
import aiida_crystal17.tests as tests
import ejplugins
import numpy as np
import pytest
from jsonextended import edict
from ase.spacegroup import crystal

#TODO parameterize tests (how do you parameterize with fixtures?)


def get_main_code(workdir):
    """get the crystal17.basic code """
    computer = tests.get_computer(workdir=workdir)
    # get code
    code = tests.get_code(entry_point='crystal17.main', computer=computer)

    return code


def test_prepare(new_database, new_workdir):
    """test preparation of inputs"""
    code = get_main_code(new_workdir)

    from aiida.orm import DataFactory, CalculationFactory
    StructureData = DataFactory('structure')
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    instruct = StructureData(ase=atoms)

    calc_cls = CalculationFactory('crystal17.main')
    calc_cls.prepare_inputs(
        {}, instruct, settings={"crystal.system": "triclinic"}, flattened=True)


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

    # MgO
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    instruct = StructureData(ase=atoms)

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
        print([
            os.path.basename(p)
            for p in glob.glob(os.path.join(subfolder.abspath, "*"))
        ])
        with open(os.path.join(subfolder.abspath, "main.gui")) as f:
            print(f.read())
