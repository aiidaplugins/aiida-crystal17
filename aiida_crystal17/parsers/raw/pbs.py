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


def parse_pbs_stderr(file_handle):
    """look for errors originating from PBS pro std error messages"""
    for line in file_handle.readlines():
        if 'PBS: job killed: mem' in line:
            return 'ERROR_OUT_OF_MEMORY'
        if 'PBS: job killed: vmem' in line:
            return 'ERROR_OUT_OF_VMEMORY'
        if 'PBS: job killed: walltime' in line:
            return 'ERROR_OUT_OF_WALLTIME'

    return None
