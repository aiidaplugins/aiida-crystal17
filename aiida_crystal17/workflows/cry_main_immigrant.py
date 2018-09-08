"""a workflow to immigrate previously run CRYSTAL17 computations into Aiida"""
from aiida_crystal17.parsers.geometry import create_gui_from_struct
from aiida_crystal17.parsers.mainout_parse import parse_mainout
from aiida_crystal17.parsers.migrate import create_inputs

from aiida.parsers.exceptions import ParsingError
from aiida.common.datastructures import calc_states


# pylint: disable=too-many-locals
def migrate_as_main(input_path, output_path, resources=None):
    """ migrate existing CRYSTAL17 calculation as a WorkCalculation,
    which imitates a ``crystal17.main`` calculation

    :param input_path: path to .d12
    :param output_path: path to .out
    :param resources: a dict of of job resource parameters
    :raises aiida.parsers.exceptions.ParsingError: if the input parsing fails
    :raises aiida.parsers.exceptions.OutputParsingError: if the output parsing fails
    :return: the calculation node
    :rtype: from aiida.orm.WorkCalculation

    """
    from aiida.work.workchain import WorkChain
    from aiida_crystal17.calculations.cry_main import CryMainCalculation
    from aiida_crystal17.parsers.cry_basic import CryBasicParser

    calc = CryMainCalculation()
    parser_cls = CryBasicParser

    resources = {} if resources is None else resources

    inputs = create_inputs(input_path, output_path)

    _, atomid_kind_map = create_gui_from_struct(inputs['structure'],
                                                inputs['settings'].get_dict())

    outparam, outarray, outstructure, psuccess, perrors = parse_mainout(
        output_path,
        parser_class=parser_cls.__name__,
        atomid_kind_map=atomid_kind_map)

    if perrors or not psuccess:
        raise ParsingError(
            "the parser failed, raising the following errors:\n{}".format(
                "\n\t".join(perrors)))

    inputs_dict = {
        calc.get_linkname("parameters"): inputs['parameters'],
        calc.get_linkname("structure"): inputs['structure'],
        calc.get_linkname("settings"): inputs['settings']
    }
    for el, basis in inputs["basis"].items():
        inputs_dict[calc.get_linkname_basisset(el)] = basis

    print(inputs_dict)

    outputs_dict = {parser_cls.get_linkname_outparams(): outparam}
    if outstructure:
        outputs_dict[parser_cls.get_linkname_outstructure()] = outstructure
    if outarray:
        outputs_dict[parser_cls.get_linkname_outarrays()] = outarray

    # TODO create output Folder containing input & output files (with correct names)

    # we create a bespoke workchain with the required inputs and outputs
    class CryMainImmigrant(WorkChain):
        @classmethod
        def define(cls, spec):
            super(CryMainImmigrant, cls).define(spec)
            for name in inputs_dict:
                spec.input(name)
            spec.outline(cls.compute, )
            for oname in outputs_dict:
                spec.output(oname)

        # pylint: disable=protected-access
        def compute(self):

            for name, data in outputs_dict.items():
                self.out(name, data)

            # TODO is there a better (more formal) way to set attributes of a WorkCalculation
            self.calc._updatable_attributes = tuple(
                list(self.calc._updatable_attributes) +
                ["jobresource_params", "parser"])
            self.calc._set_attr("state", calc_states.FINISHED)
            self.calc._set_attr("jobresource_params", resources)
            self.calc._set_attr("parser", parser_cls.__name__)

    try:
        # aiida version 1
        from aiida.work.launch import run_get_node
        _, calcnode = run_get_node(CryMainImmigrant, **inputs_dict)
    except ImportError:
        # aiida version 0.12
        workchain = CryMainImmigrant.new_instance(inputs=inputs_dict)
        workchain.run_until_complete()
        calcnode = workchain.calc

    calcnode.label = "CryMainImmigrant"
    calcnode.description = "an immigrated CRYSTAL17 calculation into the {} format".format(
        calc.__class__)

    return calcnode
