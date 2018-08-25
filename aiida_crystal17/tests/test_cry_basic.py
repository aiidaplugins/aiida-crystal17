""" Tests for basic CRYSTAL17 calculation

"""
import os

import aiida_crystal17.tests as tests
import pytest
# from aiida_crystal17.calculations.cry_basic import CryBasicCalculation


def test_submit(new_database):
    """Test submitting a calculation"""
    from aiida.orm.data.singlefile import SinglefileData
    from aiida.common.folders import SandboxFolder

    # get code
    code = tests.get_code(
        entry_point='crystal17.basic')

    # Prepare input parameters
    infile = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'mgo_sto3g.d12'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)

    calc.store_all()

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))


@pytest.mark.process_execution
def test_process(new_database):
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""
    from aiida.orm.data.singlefile import SinglefileData

    # get code
    code = tests.get_code(
        entry_point='crystal17.basic')

    # Prepare input parameters
    infile = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'mgo_sto3g.d12'))

    # set up calculation
    calc = code.new_calc()
    # calc.label = "aiida_crystal17 test"
    # calc.description = "Test job submission with the aiida_crystal17 plugin"
    # calc.set_max_wallclock_seconds(30)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.use_input_file(infile)

    calc.store_all()

    # test process execution
    tests.test_calculation_execution(calc, check_paths=[calc._DEFAULT_OUTPUT_FILE])


# TODO test that calculation completed successfully


# def test_output(test_data):
#     """Test submitting a calculation"""
#     from aiida.orm.data.singlefile import SinglefileData
#     try:
#         from aiida.work.run import submit, run
#     except ImportError:
#         from aiida.work.launch import submit, run
#
#     code = tests.get_code(
#         entry_point='crystal17.basic')
#
#     infile = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'mgo_sto3g.d12'))
#
#     # set up calculation
#     calc = code.new_calc()
#     # calc.label = "aiida_crystal17 test"
#     # calc.description = "Test job submission with the aiida_crystal17 plugin"
#     # calc.set_max_wallclock_seconds(30)
#     # calc.set_withmpi(False)
#     # calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
#     #
#     # calc.use_input_file(infile)
#
#     # calc.store_all()
#
#     inputs = {"_options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
#                           "withmpi": False, "max_wallclock_seconds": False},
#               "_label": "aiida_crystal17 test",
#               "_description": "Test job submission with the aiida_crystal17 plugin",
#               "input_file": infile,
#               "code": code}
#
#     print("running")
#     run(calc.__class__.process(), **inputs)
#     # print("submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
#     #     calc.uuid, calc.dbnode.pk))


# def test_output2(test_data):
#     """Test calculation output"""
#     from aiida.orm.data.singlefile import SinglefileData
#     from aiida.work.workchain import WorkChain, ToContext, append_
#     from aiida.orm.utils import CalculationFactory
#     from aiida.common.exceptions import MissingPluginError
#     from aiida_quantumespresso.utils.mapping import prepare_process_inputs
#
#     try:
#         from aiida.work.run import submit
#     except ImportError:
#         from aiida.work.launch import submit
#
#     class RetrieveOutput(WorkChain):
#
#         @classmethod
#         def define(cls, spec):
#             super(RetrieveOutput, cls).define(spec)
#             spec.input('infile')
#             spec.outline(
#                 cls.submit_calc,
#                 cls.inspect_calc
#             )
#
#         def submit_calc(self):
#             # set up calculation
#
#             code = tests.get_code(
#                 entry_point='crystal17.basic')
#             calc = code.new_calc()  # type: CryBasicCalculation
#
#             # plugin_name = code.get_input_plugin_name()
#             # if plugin_name is None:
#             #     raise ValueError("You did not specify an input plugin "
#             #                      "for this code")
#             # try:
#             #     calc_cls = CalculationFactory(plugin_name)
#             #
#             # except MissingPluginError:
#             #     raise MissingPluginError("The input_plugin name for this code is "
#             #                              "'{}', but it is not an existing plugin"
#             #                              "name".format(plugin_name))
#
#
#             calc.label = "aiida_crystal17 test"
#             calc.description = "Test job submission with the aiida_crystal17 plugin"
#             calc.set_max_wallclock_seconds(30)
#             calc.set_withmpi(False)
#             calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
#             calc.use_input_file(infile)
#
#             # calc.store_all()
#             #
#             # inputs = prepare_process_inputs({"_options": {"resources": None}})
#             # inputs._options.resources = {"num_machines": 1, "num_mpiprocs_per_machine": 1}
#             #
#             # print(inputs)
#
#
#             # calc_inputs = {
#             #     "max_wallclock_seconds": 30,
#             #     "withmpi": False,
#             #     "jobresource_params": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
#             # }
#             #
#             # calc_inputs = prepare_process_inputs(calc_inputs)
#
#             print(list(calc.attrs()))
#
#             # future = submit(calc.process(), inputs)
#             print(calc.process().spec().get_inputs_template())
#             inputs = {"_options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
#                                   "withmpi": False, "max_wallclock_seconds": False},
#                       "_label": "aiida_crystal17 test",
#                       "_description": "Test job submission with the aiida_crystal17 plugin",
#                       # "input_file": infile,
#                       "code": code}
#
#             future = submit(calc.process(), **inputs)
#
#             return ToContext(calculation=append_(future))
#
#             # return self.to_context(calculation=future)
#
#         def inspect_calc(self):
#             assert self.ctx.calculation.is_finished_ok
#
#     infile = SinglefileData(file=os.path.join(tests.TEST_DIR, "input_files", 'mgo_sto3g.d12'))
#
#     RetrieveOutput.run(infile=infile)
#
#
#
#
#
