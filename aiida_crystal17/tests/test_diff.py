""" Tests for diff calculation

"""
import os

import aiida_crystal17.tests as tests
import pytest


@pytest.fixture(scope='function')
def test_data(aiida_profile):
    # load my test data
    yield
    aiida_profile.reset_db()


def test_submit(test_data):
    """Test submitting a calculation"""
    from aiida.orm.data.singlefile import SinglefileData
    from aiida.work.run import submit, run

    code = tests.get_code(
        entry_point='diff')  # TODO this should go in setup

    # Prepare input parameters
    from aiida.orm import DataFactory
    DiffParameters = DataFactory('diff')
    parameters = DiffParameters({'ignore-case': True})

    file1 = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'file1.txt'))
    file2 = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'file2.txt'))

    # set up calculation
    calc = code.new_calc()
    calc.label = "aiida_crystal17 test"
    calc.description = "Test job submission with the aiida_crystal17 plugin"
    calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_parameters(parameters)
    calc.use_file1(file1)
    calc.use_file2(file2)

    calc.store_all()
    calc.submit()
    print("submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid, calc.dbnode.pk))

    # TODO test that calculation completed successfully

    # inputs = {"_options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
    #                       "withmpi": False, "max_wallclock_seconds": False},
    #           "_label": "aiida_crystal17 test",
    #           "_description": "Test job submission with the aiida_crystal17 plugin",
    #           "file1": file1, "file2": file2, "parameters": parameters,
    #           "code": code}
    #
    # run(calc.__class__.process(), **inputs)

