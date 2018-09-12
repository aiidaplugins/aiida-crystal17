""" Tests for basic CRYSTAL17 calculation

"""
import glob
import os

import aiida_crystal17
import aiida_crystal17.tests.utils as tests
import ejplugins
import pytest
from aiida_crystal17.tests import TEST_DIR
from aiida_crystal17.utils import aiida_version, cmp_version, run_get_node
from ase.spacegroup import crystal
from jsonextended import edict


def get_main_code(workdir, configure=False):
    """get the crystal17.basic code """
    computer = tests.get_computer(workdir=workdir, configure=configure)
    # get code
    code = tests.get_code(entry_point='crystal17.main', computer=computer)

    return code


def test_prepare_and_validate(new_database, new_workdir):
    """test preparation of inputs"""
    code = get_main_code(new_workdir)

    inparams = {"scf.k_points": (8, 8)}

    from aiida.orm import DataFactory, CalculationFactory
    StructureData = DataFactory('structure')

    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    instruct = StructureData(ase=atoms)

    from aiida_crystal17.workflows.symmetrise_3d_struct import run_symmetrise_3d_structure
    instruct, settings = run_symmetrise_3d_structure(instruct)

    calc_cls = CalculationFactory('crystal17.main')
    calc_cls.prepare_and_validate(inparams, instruct, settings, flattened=True)


def test_submit_mgo(new_database, new_workdir):
    """Test submitting a calculation"""
    from aiida.orm import DataFactory
    ParameterData = DataFactory('parameter')
    StructureData = DataFactory('structure')
    BasisSetData = DataFactory('crystal17.basisset')
    from aiida.common.folders import SandboxFolder

    # get code
    code = get_main_code(new_workdir)

    # Prepare input parameters
    inparams = ParameterData(dict={
        "title": "MgO Bulk",
        "scf": {
            "k_points": (8, 8)
        }
    })

    # MgO
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    instruct = StructureData(ase=atoms)

    from aiida_crystal17.workflows.symmetrise_3d_struct import run_symmetrise_3d_structure
    instruct, settings = run_symmetrise_3d_structure(instruct)

    mg_basis, _ = BasisSetData.get_or_create(
        os.path.join(TEST_DIR, "input_files", "sto3g", 'sto3g_Mg.basis'))
    o_basis, _ = BasisSetData.get_or_create(
        os.path.join(TEST_DIR, "input_files", "sto3g", 'sto3g_O.basis'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_parameters(inparams)
    calc.use_structure(instruct)
    calc.use_settings(settings)
    calc.use_basisset(mg_basis, "Mg")
    calc.use_basisset(o_basis, "O")

    calc.store_all()

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))
        print([
            os.path.basename(p)
            for p in glob.glob(os.path.join(subfolder.abspath, "*"))
        ])
        with open(os.path.join(subfolder.abspath,
                               calc._DEFAULT_INPUT_FILE)) as f:
            input_content = f.read()
        with open(
                os.path.join(subfolder.abspath,
                             calc._DEFAULT_EXTERNAL_FILE)) as f:
            gui_content = f.read()

    expected_input = """MgO Bulk
EXTERNAL
END
12 3
1 0 3  2.  0.
1 1 3  8.  0.
1 1 3  2.  0.
8 2
1 0 3  2.  0.
1 1 3  6.  0.
99 0
END
SHRINK
8 8
END
"""

    assert input_content == expected_input

    expected_gui = """3 5 6
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
 -2.105000000E+00  -2.105000000E+00   0.000000000E+00
 -2.105000000E+00   0.000000000E+00  -2.105000000E+00
48
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
 -2.105000000E+00   0.000000000E+00  -2.105000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
 -2.105000000E+00  -4.210000000E+00  -2.105000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
 -2.105000000E+00   0.000000000E+00  -2.105000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
 -2.105000000E+00  -4.210000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
 -2.105000000E+00   0.000000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
 -2.105000000E+00  -4.210000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00  -4.210000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
 -2.105000000E+00   0.000000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00  -4.210000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
 -2.105000000E+00  -4.210000000E+00  -2.105000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00  -4.210000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00  -4.210000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00  -4.210000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
 -2.105000000E+00  -2.105000000E+00  -4.210000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.105000000E+00  -2.105000000E+00
2
 12  -2.105000000E+00  -2.105000000E+00  -4.210000000E+00
  8  -2.105000000E+00  -2.105000000E+00  -2.105000000E+00
225 48
"""

    assert gui_content == expected_gui


def test_submit_nio_afm(new_database, new_workdir):
    """Test submitting a calculation"""
    from aiida.orm import DataFactory
    StructureData = DataFactory('structure')
    from aiida_crystal17.data.basis_set import upload_basisset_family
    from aiida.common.folders import SandboxFolder

    # get code
    code = get_main_code(new_workdir)

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 30,
        "scf.post_scf": ["PPAN"]
    }

    # Ni0
    atoms = crystal(
        symbols=[28, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.164, 4.164, 4.164, 90, 90, 90])
    atoms.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
    instruct = StructureData(ase=atoms)

    settings = {"kinds.spin_alpha": ["Ni1"], "kinds.spin_beta": ["Ni2"]}

    from aiida_crystal17.workflows.symmetrise_3d_struct import run_symmetrise_3d_structure
    instruct, settings = run_symmetrise_3d_structure(instruct, settings)

    upload_basisset_family(
        os.path.join(TEST_DIR, "input_files", "sto3g"),
        "sto3g",
        "minimal basis sets",
        stop_if_existing=True,
        extension=".basis")

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    params = calc.prepare_and_validate(params, instruct, settings, "sto3g",
                                       True)

    calc.use_parameters(params)
    calc.use_structure(instruct)
    calc.use_settings(settings)
    calc.use_basisset_from_family("sto3g")

    calc.store_all()

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))
        print([
            os.path.basename(p)
            for p in glob.glob(os.path.join(subfolder.abspath, "*"))
        ])
        with open(os.path.join(subfolder.abspath,
                               calc._DEFAULT_INPUT_FILE)) as f:
            input_content = f.read()
        with open(
                os.path.join(subfolder.abspath,
                             calc._DEFAULT_EXTERNAL_FILE)) as f:
            gui_content = f.read()

        print(input_content)
        print()
        print(gui_content)

    expected_input = """NiO Bulk with AFM spin
EXTERNAL
END
28 5
1 0 3  2.  0.
1 1 3  8.  0.
1 1 3  8.  0.
1 1 3  2.  0.
1 3 3  8.  0.
8 2
1 0 3  2.  0.
1 1 3  6.  0.
99 0
END
UHF
SHRINK
8 8
ATOMSPIN
2
1 1
2 -1
FMIXING
30
SPINLOCK
0 15
PPAN
END
"""

    assert input_content == expected_input

    expected_gui = """3 1 4
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
  0.000000000E+00  -2.082000000E+00   2.082000000E+00
 -4.164000000E+00   0.000000000E+00   0.000000000E+00
16
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
 -1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00   1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00  -1.000000000E+00
  0.000000000E+00  -2.082000000E+00  -2.082000000E+00
  1.000000000E+00   0.000000000E+00   0.000000000E+00
  0.000000000E+00  -1.000000000E+00   0.000000000E+00
  0.000000000E+00   0.000000000E+00   1.000000000E+00
  0.000000000E+00   0.000000000E+00   0.000000000E+00
4
 28  -2.549714636E-16  -2.082000000E+00  -2.082000000E+00
 28  -2.082000000E+00  -2.082000000E+00   4.440892099E-16
  8  -2.082000000E+00  -2.082000000E+00  -2.082000000E+00
  8  -1.274857318E-16  -2.082000000E+00   4.440892099E-16
123 16
"""

    assert gui_content == expected_gui


def test_parser_with_init_struct(new_database, new_workdir):
    """ Test the parser

    """
    from aiida.parsers import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.orm import DataFactory

    code = get_main_code(new_workdir)

    calc = code.new_calc()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    from aiida.orm.data.structure import StructureData
    struct = StructureData()
    struct.append_atom(position=[0, 0, 0], symbols="Mg", name="Mgx")
    struct.append_atom(position=[0.5, 0.5, 0.5], symbols="O", name="Ox")
    calc.use_structure(struct)

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("crystal17.basic")
    parser = parser_cls(calc)

    with SandboxFolder() as folder:
        main_out_path = os.path.join(
            os.path.dirname(tests.__file__), "output_files",
            "mgo_sto3g_scf.crystal.out")
        with open(main_out_path) as f:
            folder.create_file_from_filelike(f, "main.out")

        fdata = DataFactory("folder")()
        fdata.replace_with_folder(folder.abspath)

        mock_retrieved = {calc._get_linkname_retrieved(): fdata}
        success, node_list = parser.parse_with_retrieved(mock_retrieved)

    assert success

    node_dict = dict(node_list)
    assert set(['output_parameters', 'output_settings',
                'output_structure']) == set(node_dict.keys())

    expected_params = {
        'parser_version': str(aiida_crystal17.__version__),
        'ejplugins_version': str(ejplugins.__version__),
        'parser_class': 'CryBasicParser',
        'parser_warnings': [],
        'errors': [],
        'warnings': [],
        'energy': -2.7121814374931E+02 * 27.21138602,
        'energy_units': 'eV',  # hartree to eV
        'calculation_type': 'restricted closed shell',
        'calculation_spin': False,
        'wall_time_seconds': 3,
        'number_of_atoms': 2,
        'number_of_assymetric': 2,
        'scf_iterations': 7,
        'volume': 18.65461527264623,
    }

    assert edict.diff(
        node_dict['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}

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
            'properties': {
                'kind_name': 'Mgx'
            },
            'species': [{
                'element': 'Mg',
                'occu': 1.0
            }],
            'xyz': [0.0, 0.0, 0.0]
        }, {
            'abc': [0.5, 0.5, 0.5],
            'label': 'O',
            'properties': {
                'kind_name': 'Ox'
            },
            'species': [{
                'element': 'O',
                'occu': 1.0
            }],
            'xyz': [2.105, 2.105, 2.105]
        }]
    }

    output_struct = node_dict[
        'output_structure'].get_pymatgen_structure().as_dict()
    # in later version of pymatgen only
    if "charge" in output_struct:
        output_struct.pop("charge")

    assert edict.diff(output_struct, expected_struct, np_allclose=True) == {}


@pytest.mark.timeout(30)
@pytest.mark.process_execution
@pytest.mark.skipif(
    aiida_version() < cmp_version('1.0.0a1'),
    reason='process hangs on TOSUBMIT state')
def test_full_run_nio_afm(new_database, new_workdir):
    """Test running a calculation"""
    """Test submitting a calculation"""
    from aiida.orm import DataFactory
    from aiida.common.datastructures import calc_states
    StructureData = DataFactory('structure')
    from aiida_crystal17.data.basis_set import upload_basisset_family, get_basissets_from_structure

    # get code
    code = get_main_code(new_workdir, configure=True)

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 30,
        "scf.post_scf": ["PPAN"]
    }

    # Ni0
    atoms = crystal(
        symbols=[28, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.164, 4.164, 4.164, 90, 90, 90])
    atoms.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
    instruct = StructureData(ase=atoms)

    settings = {"kinds.spin_alpha": ["Ni1"], "kinds.spin_beta": ["Ni2"]}

    from aiida_crystal17.workflows.symmetrise_3d_struct import run_symmetrise_3d_structure
    instruct, settings = run_symmetrise_3d_structure(instruct, settings)

    upload_basisset_family(
        os.path.join(TEST_DIR, "input_files", "sto3g"),
        "sto3g",
        "minimal basis sets",
        stop_if_existing=True,
        extension=".basis")
    # basis_map = BasisSetData.get_basis_group_map("sto3g")

    # set up calculation
    calc = code.new_calc()

    params = calc.prepare_and_validate(params, instruct, settings, "sto3g",
                                       True)

    # set up calculation
    calc = code.new_calc()

    inputs_dict = {
        "parameters":
        params,
        "structure":
        instruct,
        "settings":
        settings,
        "basisset":
        get_basissets_from_structure(instruct, "sto3g", by_kind=False),
        "code":
        code,
        "options": {
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1
            },
            "withmpi": False,
            "max_wallclock_seconds": 30
        }
    }

    process = calc.process()

    calcnode = run_get_node(process, inputs_dict)

    print(calcnode)

    assert '_aiida_cached_from' not in calcnode.extras()

    try:
        print(calcnode.out.output_parameters.get_dict())
    except AttributeError:
        pass

    assert calcnode.get_state() == calc_states.FINISHED

    assert set(calcnode.get_outputs_dict().keys()).issuperset(
        ['output_structure', 'output_parameters', 'retrieved'])

    expected_params = {
        'parser_version': str(aiida_crystal17.__version__),
        'ejplugins_version': str(ejplugins.__version__),
        'number_of_atoms': 4,
        'errors': [],
        'warnings': [],
        'energy': -85124.8936673389,
        'number_of_assymetric': 4,
        'volume': 36.099581472,
        'scf_iterations': 13,
        'energy_units': 'eV',
        'calculation_type': 'unrestricted open shell',
        'parser_warnings': [],
        'wall_time_seconds': 187,
        'parser_class': 'CryBasicParser',
        'calculation_spin': True,
        'mulliken_spin_total': 0.0,
        'mulliken_spins': [3.057, -3.057, -0.072, 0.072],
        'mulliken_electrons': [27.602, 27.603, 8.398, 8.397],
        'mulliken_charges': [0.398, 0.396999999999998, -0.398, -0.397]
    }

    print(calcnode.get_outputs_dict()['output_parameters'].get_dict())

    assert edict.diff(
        calcnode.get_outputs_dict()['output_parameters'].get_dict(),
        expected_params,
        np_allclose=True) == {}
