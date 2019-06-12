# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin for PBSPro.
This has been tested on PBSPro v. 12.
"""
from __future__ import print_function
from __future__ import division

from __future__ import absolute_import
import logging
from aiida.schedulers.plugins.pbsbaseclasses import PbsBaseClass
from aiida.schedulers.datastructures import JobResource

_LOGGER = logging.getLogger(__name__)

# This maps PbsPro status letters to our own status list

# List of states from the man page of qstat:
# B  Array job has at least one subjob running.
# E  Job is exiting after having run.
# F  Job is finished.
# H  Job is held.
# M  Job was moved to another server.
# Q  Job is queued.
# R  Job is running.
# S  Job is suspended.
# T  Job is being moved to new location.
# U  Cycle-harvesting job is suspended due to  keyboard  activity.
# W  Job is waiting for its submitter-assigned start time to be reached.
# X  Subjob has completed execution or has been deleted.


class ICLJobResource(JobResource):
    """
    Base class for PBS job resources on the ICL (cx) HPCs
    """
    _default_fields = (
        'num_machines',
        'num_cores_per_machine'
    )

    @classmethod
    def get_valid_keys(cls):
        """
        Return a list of valid keys to be passed to the __init__
        """
        return super(ICLJobResource, cls).get_valid_keys() + []

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """
        Return True if this JobResource accepts a 'default_mpiprocs_per_machine'
        key, False otherwise.
        """
        return False

    def __init__(self, **kwargs):
        """
        Initialize the job resources from the passed arguments (the valid keys can be
        obtained with the function self.get_valid_keys()).

        Should raise only ValueError or TypeError on invalid parameters.
        """
        super(ICLJobResource, self).__init__()

        if 'num_machines' not in kwargs:
            raise TypeError('num_machines must be specified')
        if 'num_cores_per_machine' not in kwargs:
            raise TypeError('num_cores_per_machine must be specified')

        try:
            self.num_machines = int(kwargs.pop('num_machines'))
        except ValueError:
            raise ValueError("num_machines must an integer")

        try:
            self.num_cores_per_machine = int(kwargs.pop('num_cores_per_machine'))
        except ValueError:
            raise ValueError("num_cores_per_machine must an integer")

        if kwargs:
            raise TypeError("The following parameters were not recognized for "
                            "the JobResource: {}".format(kwargs.keys()))

        if self.num_machines <= 0:
            raise ValueError("num_machine must be >= 1")
        if self.num_cores_per_machine <= 0:
            raise ValueError("num_cores_per_machine must be >= 1")

        self.num_mpiprocs_per_machine = None


class PbsproICLScheduler(PbsBaseClass):
    """
    Subclass to support the PBSPro scheduler
    (http://www.pbsworks.com/).
    But altered to fit the Imperial College London cx scheduler spec,
    which requires ncpus and mem to be defines
    See:
    https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/computing/high-throughput-computing/job-sizing/

    I redefine only what needs to change from the base class
    """

    # I don't need to change this from the base class
    _job_resource_class = ICLJobResource

    # For the time being I use a common dictionary, should be sufficient
    # for the time being, but I can redefine it if needed.
    # _map_status = _map_status_pbs_common

    def _get_resource_lines(self, num_machines, num_mpiprocs_per_machine,
                            num_cores_per_machine, max_memory_kb,
                            max_wallclock_seconds):
        """
        Return the lines for machines, memory and wallclock relative
        to pbspro.
        """
        # Note: num_cores_per_machine is not used here but is provided by
        #       the parent class ('_get_submit_script_header') method

        return_lines = []

        select_string = "select={}".format(num_machines)

        if num_cores_per_machine is not None and num_cores_per_machine > 0:
            select_string += ":ncpus={}".format(num_cores_per_machine)
        else:
            raise ValueError(
                "num_cores_per_machine must be greater than 0! It is instead '{}'".format(num_cores_per_machine))

        if max_wallclock_seconds is not None:
            try:
                tot_secs = int(max_wallclock_seconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError("max_wallclock_seconds must be "
                                 "a positive integer (in seconds)! It is instead '{}'"
                                 "".format(max_wallclock_seconds))
            hours = tot_secs // 3600
            tot_minutes = tot_secs % 3600
            minutes = tot_minutes // 60
            seconds = tot_minutes % 60
            return_lines.append(
                "#PBS -l walltime={:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))

        if not max_memory_kb:
            max_memory_kb = 1000  # use a default memory of 1gb

        try:
            virtual_memory_gb = int(max_memory_kb / 1000.)
            if virtual_memory_gb <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("max_memory_kb must be "
                             "a positive integer (in kB) >= 1000 kb! It is instead '{}'"
                             "".format((max_memory_kb)))
        select_string += ":mem={}gb".format(virtual_memory_gb)

        return_lines.append("#PBS -l {}".format(select_string))
        return return_lines
