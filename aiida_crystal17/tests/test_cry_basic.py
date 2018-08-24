""" Tests for basic CRYSTAL17 calculation

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

    code = tests.get_code(
        entry_point='crystal17.basic')

    infile = SinglefileData(file=os.path.join(tests.TEST_DIR, 'mgo_sto3g.d12'))

    # set up calculation
    calc = code.new_calc()
    calc.label = "aiida_crystal17 test"
    calc.description = "Test job submission with the aiida_crystal17 plugin"
    calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)

    calc.store_all()
    calc.submit()
    print("submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid, calc.dbnode.pk))



