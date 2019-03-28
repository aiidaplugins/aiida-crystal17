"""a workflow to immigrate previously run CRYSTAL17 computations into Aiida"""
import io
import os

from aiida.common.exceptions import ParsingError
from aiida.engine import WorkChain
from aiida_crystal17.parsers.mainout_parse import parse_mainout
from aiida_crystal17.parsers.migrate import create_builder
# from aiida.common.datastructures import calc_states
from aiida.engine import run_get_node


# pylint: disable=too-many-locals
def migrate_as_main(work_dir,
                    input_rel_path,
                    output_rel_path,
                    code,
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
    from aiida.orm.nodes import FolderData
    from aiida.plugins.factories import ParserFactory

    # TODO optionally use transport to remote work directory
    if not os.path.exists(work_dir):
        raise IOError("work_dir doesn't exist: {}".format(work_dir))
    input_path = os.path.join(work_dir, input_rel_path)
    if not os.path.exists(input_path):
        raise IOError("input_path doesn't exist: {}".format(input_path))
    output_path = os.path.join(work_dir, output_rel_path)
    if not os.path.exists(output_path):
        raise IOError("output_path doesn't exist: {}".format(output_path))

    builder = create_builder(input_path, output_path)
    builder.code = code
    builder.metadata.options.resources = {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1
            } if resources is None else resources
    calc = builder.process_class(inputs=builder)
    parser_cls = ParserFactory(calc.metadata.options.parser_name)

    with io.open(output_path) as file_obj:
        parser_result = parse_mainout(
            file_obj,
            parser_class=parser_cls.__name__,
            init_struct=builder.structure,
            init_settings=builder.symmetry)

    perrors = parser_result.nodes.results.get_attribute("errors")
    perrors = parser_result.nodes.results.get_attribute("parser_errors")

    if perrors or not parser_result.success:
        raise ParsingError(
            "the parser failed, raising the following errors:\n{}".format(
                "\n\t".join(perrors)))

    folder = FolderData()
    folder.put_object_from_file(
        input_path, calc.metadata.options.input_file_name)
    folder.put_object_from_file(
        output_path, calc.metadata.options.output_main_file_name)

    # # create links from existing nodes to inputs
    # input_links = {} if not input_links else input_links
    # for key, nodes_dict in input_links.items():
    #     _run_dummy_workchain(
    #         nodes_dict,
    #         {key: inputs[key]},
    #     )

    parser_result.nodes.results
    parser_result.nodes.structure
    parser_result.nodes.symmetry
    parser_result.nodes.folder = folder

    

    calc_node.label = "CryMainImmigrant"
    calc_node.description = "an immigrated CRYSTAL17 calculation into the {} format".format(
        calc.__class__)

    return calc_node


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

    calcnode = run_get_node(DummyProcess, inputs_dict)

    return calcnode
