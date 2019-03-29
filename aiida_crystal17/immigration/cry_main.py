"""a workflow to immigrate previously run CRYSTAL17 computations into Aiida"""
import os
import six

from aiida.orm import CalcJobNode
from aiida.common.links import LinkType
from aiida.orm import FolderData

from aiida_crystal17.parsers.main_out import parse_main_out
from aiida_crystal17.immigration.create_inputs import create_builder
from aiida_crystal17.calculations.cry_main import CryMainCalculation


def migrate_as_main(
        folder, code, input_name="main.d12", output_name="main.out",
        resources=(('num_mpiprocs_per_machine', 1), ('num_machines', 1)),
        withmpi=False,
        store_all=False,
        incoming_links=None):

    # initial calc job setup
    calc_node = CalcJobNode()
    calc_node.set_process_type("crystal17.main")
    calc_node.set_process_state("finished")
    calc_node.set_process_label(CryMainCalculation.__name__)
    calc_node.set_attribute("immigrated", True)
    calc_node.set_options({
        'resources': dict(resources),
        'withmpi': withmpi,
        'output_main_file_name': output_name,
        # 'external_file_name': 'main.gui',
        'input_file_name': input_name,
    })
    calc_node.computer = code.computer

    if isinstance(folder, six.string_types):
        input_path = os.path.join(folder, input_name)
        if not os.path.exists(input_path):
            raise IOError("input_path doesn't exist: {}".format(input_path))
        output_path = os.path.join(folder, output_name)
        if not os.path.exists(output_path):
            raise IOError("output_path doesn't exist: {}".format(output_path))
        folder = FolderData()
        folder.put_object_from_file(input_path, input_name)
        folder.put_object_from_file(output_path, output_name)

    builder = create_builder(
        folder, input_name=input_name, output_name=output_name, code=code)

    calc_node.add_incoming(
        builder.code, LinkType.INPUT_CALC, "code")
    calc_node.add_incoming(
        builder.structure, LinkType.INPUT_CALC, "structure")
    calc_node.add_incoming(
        builder.parameters, LinkType.INPUT_CALC, "parameters")
    calc_node.add_incoming(
        builder.symmetry, LinkType.INPUT_CALC, "symmetry")
    for key, basisset in builder.basissets.items():
        calc_node.add_incoming(
            basisset, LinkType.INPUT_CALC, "basissets_{}".format(key))

    if store_all:
        calc_node.store_all()

    with folder.open(output_name) as file_obj:
        parser_result = parse_main_out(
            file_obj,
            parser_class="CryMainParser",
            init_struct=builder.structure,
            init_settings=builder.symmetry)

    calc_node.set_exit_status(parser_result.exit_code.status)
    if parser_result.exit_code.message is not None:
        calc_node.set_exit_message(parser_result.exit_code.message)

    for link_name, node in parser_result.nodes.items():
        node.add_incoming(calc_node, LinkType.CREATE, link_name)
        if store_all and not node.is_stored:
            node.store()

    folder.add_incoming(
        calc_node, LinkType.CREATE, CryMainCalculation.link_label_retrieved)
    if store_all and not folder.is_stored:
        folder.store()

    calc_node.label = "CryMainImmigrant"
    calc_node.description = (
        "an immigrated CRYSTAL17 calculation into the {} format").format(
        CryMainCalculation)

    return calc_node
