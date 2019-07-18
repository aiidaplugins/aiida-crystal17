"""
submit a test parallel run to Imperial HPC CX1

can use: `verdi run aiida_crystal17/tests/cx1_submission_tests.py`

for info on parallel calculations see:
http://tutorials.crystalsolutions.eu/tutorial.html?td=tuto_HPC&tf=tuto_hpc
"""
import os
import time

from aiida.common import NotExistent
from aiida.engine import run_get_node, submit
from aiida.manage.caching import disable_caching
from aiida.orm import Computer, Code, Group
from aiida.orm.utils.builders.computer import ComputerBuilder
from aiida.orm.utils.builders.code import CodeBuilder
from aiida.plugins import DataFactory, WorkflowFactory
from aiida.plugins.entry_point import get_entry_point

from aiida_crystal17.tests import TEST_FILES, get_test_structure

_COMPUTER_NAME = "icl_cx1_test"
_CODE_LABEL = "cry17-main-cx1_test"


def get_cx1_computer(work_dir, key_filename=None):
    try:
        computer_cx1 = Computer.objects.get(name=_COMPUTER_NAME)
    except NotExistent:
        computer_builder = ComputerBuilder(
            label=_COMPUTER_NAME,
            description='Imperial HPC cx1 tests',
            transport='ssh',
            # this scheduler overrides the behavious of the standard PbsPro scheduler
            # to use a `#PBS -l select=` line acceptable for cx1
            scheduler='pbspro_icl',
            hostname='login.cx1.hpc.ic.ac.uk',
            prepend_text='',
            append_text='',
            work_dir=work_dir,
            shebang='#!/bin/bash',
            mpiprocs_per_machine=16,
            mpirun_command='mpiexec'
        )
        computer_cx1 = computer_builder.new()
        computer_cx1.store()
        computer_cx1.configure(
            look_for_keys=True,
            key_filename=key_filename,
            timeout=60,
            allow_agent=True,
            compress=True,
            load_system_host_keys=True,
            safe_interval=5.0
        )
    return computer_cx1


def get_cx1_crystal_code(
        work_dir, exec_path,
        modules=('intel-suite/2016.3', 'mpi/intel-5.1'),
        key_filename=None):

    computer_cx1 = get_cx1_computer(work_dir, key_filename=key_filename)

    try:
        code_cry17 = Code.objects.get(label=_CODE_LABEL)
    except NotExistent:
        code_builder = CodeBuilder(
            **{
                'label': _CODE_LABEL,
                'description': 'The CRYSTAL17 code on CX1',
                'code_type': CodeBuilder.CodeType.ON_COMPUTER,
                'computer': computer_cx1,
                'prepend_text': 'module load ' + " ".join(modules),
                'append_text': '',
                'input_plugin': get_entry_point('aiida.calculations', 'crystal17.main'),
                'remote_abs_path': exec_path
            }
        )
        code_cry17 = code_builder.new()
        code_cry17.store()
    return code_cry17


def submit_nio_afm_fullopt():

    code = get_cx1_crystal_code(
        "/work/cjs14/aiida_v100b3_runs",
        ('/rds/general/user/gmallia/home/CRYSTAL17_cx1/v2/bin/Linux-mpiifort_MPP/'
         'C17-v2_mod_Xeon___mpi__intel-2018___intel-suite__2016.3/Pcrystal'),
        key_filename="/Users/cjs14/.ssh/id_rsa")

    kind_data_cls = DataFactory('crystal17.kinds')
    basis_data_cls = DataFactory('crystal17.basisset')
    upload_basisset_family = basis_data_cls.upload_basisset_family

    # Prepare input parameters
    params = {
        "title": "NiO Bulk with AFM spin",
        "geometry.optimise.type": "FULLOPTG",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 50,
        "scf.numerical.MAXCYCLE": 100,
        "scf.post_scf": ["PPAN"]
    }

    ostruct = get_test_structure("NiO_afm")

    kind_data = kind_data_cls(data={
        "kind_names": ["Ni1", "Ni2", "O"],
        "spin_alpha": [True, False, False], "spin_beta": [False, True, False]})

    sym_settings = DataFactory("dict")(
        dict={"symprec": 0.01, "compute_primitive": True})

    sym_calc = run_get_node(
        WorkflowFactory("crystal17.sym3d"), structure=ostruct,
        settings=sym_settings).node
    time.sleep(0.1)
    instruct = sym_calc.get_outgoing().get_node_by_label("structure")
    symmetry = sym_calc.get_outgoing().get_node_by_label("symmetry")

    upload_basisset_family(
        os.path.join(TEST_FILES, "basis_sets", "sto3g"),
        "sto3g",
        "minimal basis sets",
        stop_if_existing=False,
        extension=".basis")

    # set up calculation
    process_class = code.get_builder().process_class

    metadata = {
        "options": {
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 16,
            },
            'max_memory_kb': 1 * 1000,
            'max_wallclock_seconds': int(23.9 * 3600),
            'withmpi': True,
            # 'queue_name': "pqcdt"
        }}
    builder = process_class.create_builder(
        params, instruct, "sto3g", symmetry=symmetry, kinds=kind_data,
        code=code, metadata=metadata, unflatten=True)

    with disable_caching():
        calc_node = submit(builder)

    # great a group to store all the nodes we create in
    group, created = Group.objects.get_or_create(
        label="cry17_cx1_tests")  # type: Group
    group.add_nodes([code, ostruct, kind_data, sym_settings,
                     sym_calc, instruct, symmetry, calc_node])

    print("Inputs Group: {}".format(group))

    print("Calc Node ID: {}".format(calc_node.id))
    # print(calc_node.outputs.remote_folder.get_remote_path())

    return group


if __name__ == "__main__":
    submit_nio_afm_fullopt()
