# -*- coding: utf-8 -*-
"""Submit a test calculation on localhost.

Usage: verdi run submit.py

Note: This script assumes you have set up computer and code as in README.md.
"""
import os

import aiida_crystal17.tests as tests
from aiida.orm import DataFactory

code = tests.get_code(entry_point='diff')

# Prepare input parameters
DiffParameters = DataFactory('diff')
parameters = DiffParameters({'ignore-case': True})

SinglefileData = DataFactory('singlefile')
file1 = SinglefileData(file=os.path.join(tests.TEST_DIR, 'file1.txt'))
file2 = SinglefileData(file=os.path.join(tests.TEST_DIR, 'file2.txt'))

# set up calculation
calc = code.new_calc()
calc.label = "aiida_diff test"
calc.description = "Test job submission with the aiida_diff plugin"
calc.set_max_wallclock_seconds(30)
calc.set_withmpi(False)
calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

calc.use_parameters(parameters)
calc.use_file1(file1)
calc.use_file2(file2)

calc.store_all()
calc.submit()
print("submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(calc.uuid, calc.dbnode.pk))
