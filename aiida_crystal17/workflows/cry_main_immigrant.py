"""a workflow to immigrate previously run CRYSTAL17 computations into Aiida"""
import os

from aiida.parsers.exceptions import ParsingError
from aiida.work import WorkChain
from aiida_crystal17.parsers.geometry import compute_symmetry_from_structure
from aiida_crystal17.parsers.mainout_parse import parse_mainout
from aiida_crystal17.parsers.migrate import create_inputs
# from aiida.common.datastructures import calc_states


class CryMainImmigrant(WorkChain):
    """
    an immigrant calculation of CryMainCalculation
    """
    pass
    # TODO how to to set attributes of a WorkCalculation? (below works for v0.12 but not v1)
    # self.calc._updatable_attributes = tuple(
    #     list(self.calc._updatable_attributes) +
    #     ["jobresource_params", "parser"])
    # self.calc._set_attr("state", calc_states.FINISHED, stored_check=False)
    # self.calc._set_attr("jobresource_params", resources, stored_check=False)
    # self.calc._set_attr("parser", parser_cls.__name__, stored_check=False)


# pylint: disable=too-many-locals
def migrate_as_main(work_dir,
                    input_rel_path,
                    output_rel_path,
                    resources=None,
                    input_links=None):
    """ migrate existing CRYSTAL17 calculation as a WorkCalculation,
    which imitates a ``crystal17.main`` calculation

    :param work_dir: the absolute path to the directory to holding the files
    :param input_rel_path: relative path (from work_dir) to .d12 file
    :param output_rel_path: relative path (from work_dir) to .out file
    :param resources: a dict of of job resource parameters (not yet implemented)
    :param input_links: a dict of existing nodes to link inputs to (allowed keys: 'structure', 'settings', 'parameters')

    Example of input_links={'structure': {"cif_file": CifNode}},
    will create a link (via a workcalculation) from the CifNode to the input StructureData

    :raise IOError: if the work_dir or files do not exist
    :raises aiida.common.exceptions.ParsingError: if the input parsing fails
    :raises aiida.parsers.exceptions.OutputParsingError: if the output parsing fails

    :return: the calculation node
    :rtype: aiida.orm.WorkCalculation

    """
    from aiida.orm.data.folder import FolderData
    from aiida_crystal17.calculations.cry_main import CryMainCalculation
    from aiida_crystal17.parsers.cry_basic import CryBasicParser

    calc = CryMainCalculation()
    parser_cls = CryBasicParser

    # TODO optionally use transport to remote work directory
    if not os.path.exists(work_dir):
        raise IOError("work_dir doesn't exist: {}".format(work_dir))
    input_path = os.path.join(work_dir, input_rel_path)
    if not os.path.exists(input_path):
        raise IOError("input_path doesn't exist: {}".format(input_path))
    output_path = os.path.join(work_dir, output_rel_path)
    if not os.path.exists(output_path):
        raise IOError("output_path doesn't exist: {}".format(output_path))

    if resources:
        raise NotImplementedError("saving resources to ImmigrantCalculation")
    # resources = {} if resources is None else resources

    inputs = create_inputs(input_path, output_path)

    newsdata, symmdata = compute_symmetry_from_structure(
        inputs['structure'], inputs['settings'].get_dict())

    outparam, outarray, outstructure, psuccess, perrors = parse_mainout(
        output_path,
        parser_class=parser_cls.__name__,
        atom_kinds=newsdata["kinds"])

    if perrors or not psuccess:
        raise ParsingError(
            "the parser failed, raising the following errors:\n{}".format(
                "\n\t".join(perrors)))

    folder = FolderData()
    folder.add_path(input_path, calc._DEFAULT_INPUT_FILE)  # pylint: disable=protected-access
    folder.add_path(output_path, calc._DEFAULT_OUTPUT_FILE)  # pylint: disable=protected-access

    # create links from existing nodes to inputs
    input_links = {} if not input_links else input_links
    for key, nodes_dict in input_links.items():
        _run_dummy_workchain(
            nodes_dict,
            {key: inputs[key]},
        )

    # assign linknames
    inputs_dict = {
        calc.get_linkname("parameters"): inputs['parameters'],
        calc.get_linkname("structure"): inputs['structure'],
        calc.get_linkname("settings"): inputs['settings']
    }
    for el, basis in inputs["basis"].items():
        inputs_dict[calc.get_linkname_basisset(el)] = basis

    outputs_dict = {parser_cls.get_linkname_outparams(): outparam}
    if outstructure:
        outputs_dict[parser_cls.get_linkname_outstructure()] = outstructure
    if outarray:
        outputs_dict[parser_cls.get_linkname_outarrays()] = outarray
    outputs_dict["retrieved"] = folder

    calcnode = _run_dummy_workchain(inputs_dict, outputs_dict,
                                    CryMainImmigrant)

    calcnode.label = "CryMainImmigrant"
    calcnode.description = "an immigrated CRYSTAL17 calculation into the {} format".format(
        calc.__class__)

    return calcnode


def _run_dummy_workchain(inputs_dict, outputs_dict, workchain_cls=None):
    """ create a bespoke workchain with the required inputs and outputs

    :param inputs_dict: dict mapping input node names to the nodes
    :param outputs_dict: dict mapping output node names to the nodes
    :param workchain_cls: the workchain class from which to inherit
    :return: the calculation node
    """
    workchain_cls = WorkChain if workchain_cls is None else workchain_cls

    class DummyProcess(workchain_cls):
        @classmethod
        def define(cls, spec):
            super(DummyProcess, cls).define(spec)
            for name in inputs_dict:
                spec.input(name)
            spec.outline(cls.compute, )
            for oname in outputs_dict:
                spec.output(oname)

        def compute(self):
            for name, data in outputs_dict.items():
                self.out(name, data)

    try:
        # aiida version 1
        from aiida.work.launch import run_get_node
        _, calcnode = run_get_node(DummyProcess, **inputs_dict)
    except ImportError:
        # aiida version 0.12
        workchain = DummyProcess.new_instance(inputs=inputs_dict)
        workchain.run_until_complete()
        calcnode = workchain.calc

    return calcnode
