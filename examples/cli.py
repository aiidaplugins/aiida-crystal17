#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
import os

import aiida_crystal17.tests
import aiida_crystal17.tests.utils
import click

import aiida_crystal17.tests as tests


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, submit):
    """Command line interface for testing and submitting calculations.

    This script extends submit.py, adding flexibility in the selected code/computer.

    Run './cli.py --help' to see options.
    """
    from aiida.orm import Code
    code = Code.get_from_string(codelabel)

    # Prepare input parameters
    from aiida.plugins import DataFactory
    SinglefileData = DataFactory('singlefile')

    infile = SinglefileData(
        file=os.path.join(aiida_crystal17.tests.TEST_DIR, "input_files",
                          'nio_sto3g_afm.crystal.d12'))
    ingeom = SinglefileData(
        file=os.path.join(aiida_crystal17.tests.TEST_DIR, "output_files",
                          'nio_sto3g_afm.crystal.out'))

    # set up calculation
    calc = code.get_builder()
    calc.label = "aiida_crystal17 test"
    calc.description = "Test job submission with the aiida_crystal17 plugin"
    calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)
    calc.use_input_external(ingeom)

    if submit:
        calc.store_all()
        calc.submit()
        print("submitted calculation; calc=Calculation(uuid='{}') # ID={}" \
              .format(calc.uuid, calc.dbnode.pk))
    else:
        subfolder, script_filename = calc.submit_test()
        path = os.path.relpath(subfolder.abspath)
        print("Submission test successful.")
        print("Find remote folder in {}".format(path))
        print("In order to actually submit, add '--submit'")


if __name__ == '__main__':
    main()
