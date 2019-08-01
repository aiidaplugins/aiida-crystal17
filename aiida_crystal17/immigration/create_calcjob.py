#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
#
# This file is part of aiida-crystal17.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
"""
Immigrate a CalcJob that was not run using AiiDa.
"""
# TODO this should eventually by moved to aiida-core
# see aiidateam/aiida-quantumespresso#350

from __future__ import absolute_import

from aiida.common.datastructures import CalcJobState
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.engine import ProcessState
from aiida.engine.daemon.execmanager import retrieve_calculation
from aiida.engine.utils import instantiate_process
from aiida.manage.manager import get_manager


def immigrate_existing(builder, remote_data, seal=True):
    """Immigrate a Calculation that was not run using AiiDa.

    :param builder: a populated builder instance for a CalcJob
    :type builder: aiida.engine.processes.builder.ProcessBuilder
    :param remote_data: a remote data folder,
        containing the output files required for parsing
    :type remote_data: aiida.orm.RemoteData
    :param seal: whether to seal the calc node, from further attribute changes
    :type seal: bool

    :rtype: aiida.orm.CalcJobNode

    """
    # initialise calcjob
    runner = get_manager().get_runner()
    pw_calc_cls = builder._process_class
    process = instantiate_process(runner, pw_calc_cls, **builder)
    calc_node = process.node

    # prepare for submission
    with SandboxFolder() as temp_folder:
        calc_info = process.presubmit(temp_folder)  # noqa F841
        calc_node.put_object_from_tree(temp_folder.abspath, force=True)

    # link remote folder to calc_node
    if not remote_data.is_stored:
        remote_data.store()
    remote_data.add_incoming(calc_node, link_type=LinkType.CREATE, link_label='remote_folder')
    calc_node.set_remote_workdir(remote_data.get_remote_path())
    transport = remote_data.computer.get_transport()

    with SandboxFolder() as temp_retrieved:
        # retrieved output files
        retrieve_calculation(calc_node, transport, temp_retrieved.abspath)
        # parse output
        calc_node.set_state(CalcJobState.PARSING)
        exit_code = process.parse(temp_retrieved.abspath)
    # link outgoing nodes
    process.update_outputs()

    # finalise calc node
    calc_node.delete_state()
    calc_node.delete_checkpoint()
    calc_node.set_process_state(ProcessState.FINISHED)
    calc_node.set_exit_status(exit_code.status)
    calc_node.set_exit_message(exit_code.message)
    if seal:
        calc_node.seal()

    # record that the node was created via immigration
    calc_node.set_extra('immigrated', True)
    calc_node.set_extra('immigration_func', __name__)

    return calc_node
