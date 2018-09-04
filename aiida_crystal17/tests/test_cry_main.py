""" Tests for basic CRYSTAL17 calculation

"""
import glob
import os

import aiida_crystal17.tests as tests
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

    inparams = {"scf.k_points": (8, 8)}

    from aiida.orm import DataFactory, CalculationFactory
    StructureData = DataFactory('structure')
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    instruct = StructureData(ase=atoms)

    calc_cls = CalculationFactory('crystal17.main')
    calc_cls.prepare_and_validate(
        inparams,
        instruct,
        settings={"crystal.system": "triclinic"},
        flattened=True)


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

    mg_basis, _ = BasisSetData.get_or_create(
        os.path.join(tests.TEST_DIR, "input_files", "sto3g", 'sto3g_Mg.basis'))
    o_basis, _ = BasisSetData.get_or_create(
        os.path.join(tests.TEST_DIR, "input_files", "sto3g", 'sto3g_O.basis'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_parameters(inparams)
    calc.use_structure(instruct)
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

    upload_basisset_family(
        os.path.join(tests.TEST_DIR, "input_files", "sto3g"),
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

    params, settings = calc.prepare_and_validate(params, instruct, settings,
                                                 "sto3g", True)

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
