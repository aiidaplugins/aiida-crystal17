# -*- coding: utf-8 -*-
"""
Immigrate a CRYSTAL17 computation that was not run using AiiDa.
"""
import six

from aiida.common.datastructures import CalcJobState
from aiida.common.folders import Folder, SandboxFolder
from aiida.common.links import LinkType
from aiida.engine import ProcessState
from aiida.engine.utils import instantiate_process
from aiida.manage.manager import get_manager
from aiida.orm import FolderData, RemoteData
from aiida.plugins import CalculationFactory


def create_crymain(builder, folder, outfile, remote_path=None):
    """Immigrate a main Crystal calculation job that was not run using AiiDa.

    Note, it is intended that this function is used in conjunction with
    aiida_crystal17.immigration.create_inputs.populate_builder, to create the builder

    :param builder: a populated builder instance for PwCalculation
    :param folder: the folder containing the input and output files
    :type folder: aiida.common.folders.Folder or str
    :param outfile: the file name of the output file
    :type outfile: str
    :param remote_path: the path on the remote computer to the run folder
    :type remote_path: str or None

    :rtype: aiida.orm.CalcJobNode

    """
    if isinstance(folder, six.string_types):
        folder = Folder(folder)

    # initialise calcjob
    runner = get_manager().get_runner()
    pw_calc_cls = CalculationFactory('crystal17.main')
    process = instantiate_process(runner, pw_calc_cls, **builder)
    calc_node = process.node

    input_filename = process.metadata.options.input_file_name
    output_filename = process.metadata.options.output_main_file_name

    # create retrieved folder
    retrieve_list = [input_filename, output_filename]
    retrieved_files = FolderData()

    # create input file and add to retrieved
    with SandboxFolder() as temp_submission:
        process.prepare_for_submission(temp_submission)
        inpath = temp_submission.get_abs_path(input_filename)
        retrieved_files.put_object_from_file(inpath, input_filename)

    # add output files to retrieved
    retrieved_files.put_object_from_file(
        folder.get_abs_path(outfile), output_filename)

    # connect and store retrieved folder
    retrieved_files.add_incoming(calc_node, link_type=LinkType.CREATE,
                                 link_label=calc_node.link_label_retrieved)
    retrieved_files.store()
    calc_node.set_retrieve_list(retrieve_list)

    # create and connect remote data folder
    if remote_path is not None:
        calc_node.set_remote_workdir(remote_path)
        remotedata = RemoteData(computer=calc_node.computer, remote_path=remote_path)
        remotedata.add_incoming(calc_node, link_type=LinkType.CREATE,
                                link_label='remote_folder')
        remotedata.store()

    # parse output and link outgoing nodes
    calc_node.set_state(CalcJobState.PARSING)
    with SandboxFolder() as temp_retrieved:
        exit_code = process.parse(temp_retrieved.abspath)
    process.update_outputs()

    # finalise calc node
    calc_node.delete_state()
    calc_node.delete_checkpoint()
    calc_node.set_process_state(ProcessState.FINISHED)
    calc_node.set_exit_status(exit_code.status)
    calc_node.set_exit_message(exit_code.message)
    calc_node.seal()

    # record that the node was created via immigration
    calc_node.set_extra('immigrated', True)
    calc_node.set_extra('immigration_mod', __name__)
    calc_node.label = "CryMainImmigrant"
    calc_node.description = "an immigrated CRYSTAL17 calculation"

    return calc_node
