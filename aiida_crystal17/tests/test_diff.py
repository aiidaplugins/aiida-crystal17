""" Tests for diff calculation

"""
import os

import aiida_crystal17.tests as tests
import pytest


def get_diff_code(workdir):
    """get the diff code """
    computer = tests.get_computer(workdir=workdir)
    # get code
    code = tests.get_code(entry_point='diff', computer=computer)

    return code


def test_submit(new_database, new_workdir):
    """Test submitting a calculation"""
    from aiida.orm.data.singlefile import SinglefileData
    from aiida.common.folders import SandboxFolder

    # get code
    code = get_diff_code(new_workdir)

    # Prepare input parameters
    from aiida.orm import DataFactory
    DiffParameters = DataFactory('diff')
    parameters = DiffParameters({'ignore-case': True})

    file1 = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files", 'file1.txt'))
    file2 = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files", 'file2.txt'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_parameters(parameters)
    calc.use_file1(file1)
    calc.use_file2(file2)

    calc.store_all()

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))


@pytest.mark.process_execution
def test_process(new_database, new_workdir):
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""
    from aiida.orm.data.singlefile import SinglefileData

    # get code
    code = get_diff_code(new_workdir)

    # Prepare input parameters
    from aiida.orm import DataFactory
    DiffParameters = DataFactory('diff')
    parameters = DiffParameters({'ignore-case': True})

    file1 = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files", 'file1.txt'))
    file2 = SinglefileData(
        file=os.path.join(tests.TEST_DIR, "input_files", 'file2.txt'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_parameters(parameters)
    calc.use_file1(file1)
    calc.use_file2(file2)

    calc.store_all()

    # test process execution
    # for diff 0=no differences, 1=differences, >1=error
    tests.test_calculation_execution(
        calc, allowed_returncodes=(1, ), check_paths=[calc._OUTPUT_FILE_NAME])


def parser(new_database, new_workdir):
    """ Test the parser

    """
    from aiida.parsers import ParserFactory
    from aiida.common.datastructures import calc_states
    from aiida.common.folders import SandboxFolder
    from aiida.orm import DataFactory

    code = get_diff_code(new_workdir)

    calc = code.new_calc()
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.store_all()
    calc._set_state(calc_states.PARSING)

    parser_cls = ParserFactory("diff")
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
    assert set(['output_parameters',
                'output_structure']) == set(node_dict.keys())

    # TODO test that calculation completed successfully

    # inputs = {"_options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
    #                       "withmpi": False, "max_wallclock_seconds": False},
    #           "_label": "aiida_crystal17 test",
    #           "_description": "Test job submission with the aiida_crystal17 plugin",
    #           "file1": file1, "file2": file2, "parameters": parameters,
    #           "code": code}
    #
    # run(calc.__class__.process(), **inputs)
