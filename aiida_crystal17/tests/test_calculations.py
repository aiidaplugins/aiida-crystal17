""" Tests for calculations

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
    print("{}".format(test_data))  # for pylint test to pass
    from aiida.orm.data.singlefile import SinglefileData

    code = tests.get_code(
        entry_point='crystal17')  # TODO this should go in setup

    # Prepare input parameters
    from aiida.orm import DataFactory
    DiffParameters = DataFactory('crystal17')
    parameters = DiffParameters({'ignore-case': True})

    file1 = SinglefileData(file=os.path.join(tests.TEST_DIR, 'file1.txt'))
    file2 = SinglefileData(file=os.path.join(tests.TEST_DIR, 'file2.txt'))

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
