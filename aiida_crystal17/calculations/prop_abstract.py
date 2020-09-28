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
"""Plugin for running CRYSTAL17 properties computations."""
import os

from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.engine import CalcJob, CalcJobProcessSpec
from aiida.orm import FolderData, RemoteData, SinglefileData
from aiida.plugins import DataFactory


class PropAbstractCalculation(CalcJob):
    """Abstract AiiDA calculation plugin class, to run the properties17 executable.

    Subclasses must at least override methods:

    - ``define``; specifying a parser and additional input/output nodes and exit codes.
    - ``validate_parameters``
    - ``create_input_content``
    - ``get_retrieve_list``
    - ``get_retrieve_temp_list``
    """

    link_output_results = "results"
    requires_newk = True

    @classmethod
    def validate_parameters(cls, data, _):
        raise NotImplementedError

    @staticmethod
    def create_newk_lines(dct):
        """Create NEWK section of input file."""
        k_is, k_isp = dct["k_points"]
        lines = ["NEWK"]
        if isinstance(k_is, int):
            lines.append("{0} {1}".format(k_is, k_isp))
        else:
            lines.append("0 {0}\n".format(k_isp))
            lines.append("{0} {1} {2}\n".format(k_is[0], k_is[1], k_is[2]))
        lines.append("1 0")  # 1 = Fermi energy is computed
        return lines

    def create_input_content(self):
        raise NotImplementedError

    def get_retrieve_list(self):
        raise NotImplementedError

    def get_retrieve_temp_list(self):
        raise NotImplementedError

    @classmethod
    def define(cls, spec: CalcJobProcessSpec):

        super(PropAbstractCalculation, cls).define(spec)

        spec.input("metadata.options.input_file_name", valid_type=str, default="INPUT")
        spec.input("metadata.options.input_wf_name", valid_type=str, default="fort.9")
        spec.input(
            "metadata.options.stdout_file_name", valid_type=str, default="main.out"
        )

        spec.input(
            "wf_folder",
            valid_type=(FolderData, RemoteData, SinglefileData),
            required=True,
            help="the folder containing the wavefunction fort.9 file",
        )
        spec.input(
            "parameters",
            valid_type=DataFactory("dict"),
            required=True,
            validator=cls.validate_parameters,
            help="the input parameters to create the properties input file.",
        )

        # subclasses should implement
        # spec.input('metadata.options.parser_name', valid_type=str, default='crystal17.')

        # Unrecoverable errors: resources like the retrieved folder or its expected contents are missing
        spec.exit_code(
            200,
            "ERROR_NO_RETRIEVED_FOLDER",
            message="The retrieved folder data node could not be accessed.",
        )
        spec.exit_code(
            210,
            "ERROR_OUTPUT_FILE_MISSING",
            message="the main (stdout) output file was not found",
        )
        spec.exit_code(
            211,
            "ERROR_TEMP_FOLDER_MISSING",
            message="the temporary retrieved folder was not found",
        )

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(
            300,
            "ERROR_PARSING_STDOUT",
            message=(
                "An error was flagged trying to parse the " "crystal exec stdout file"
            ),
        )

        spec.exit_code(
            350,
            "ERROR_CRYSTAL_INPUT",
            message="the input file could not be read by CRYSTAL",
        )
        spec.exit_code(
            351,
            "ERROR_WAVEFUNCTION_NOT_FOUND",
            message="CRYSTAL could not find the required wavefunction file",
        )
        spec.exit_code(
            352,
            "UNIT_CELL_NOT_NEUTRAL",
            message="Possibly due to erroneous CHEMOD basis set modification",
        )
        spec.exit_code(
            353,
            "SHELL_SYMMETRY_ERROR",
            message="Possibly due to erroneous CHEMOD basis set modification",
        )
        spec.exit_code(
            354, "CHEMMOD_ERROR", message="Error in CHEMOD basis set modification"
        )

        # Significant errors but calculation can be used to restart
        spec.exit_code(
            400,
            "ERROR_OUT_OF_WALLTIME",
            message="The calculation stopped prematurely because it ran out of walltime.",
        )
        spec.exit_code(
            401,
            "ERROR_OUT_OF_MEMORY",
            message="The calculation stopped prematurely because it ran out of memory.",
        )
        spec.exit_code(
            402,
            "ERROR_OUT_OF_VMEMORY",
            message="The calculation stopped prematurely because it ran out of virtual memory.",
        )

        spec.exit_code(
            413,
            "BASIS_SET_LINEARLY_DEPENDENT",
            message="an error encountered usually during geometry optimisation",
        )
        spec.exit_code(
            414,
            "ERROR_SCF_ABNORMAL_END",
            message="an error was encountered during an SCF computation",
        )
        spec.exit_code(
            415,
            "ERROR_MPI_ABORT",
            message="an unknown error was encountered, causing the MPI to abort",
        )
        spec.exit_code(
            499,
            "ERROR_CRYSTAL_RUN",
            message="The main crystal output file flagged an unhandled error",
        )

        spec.output(
            cls.link_output_results,
            valid_type=DataFactory("dict"),
            required=True,
            help="Summary Data extracted from the output file(s)",
        )
        spec.default_output_node = cls.link_output_results

    def prepare_for_submission(self, tempfolder):
        """This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """

        input_content = self.create_input_content()
        with tempfolder.open(self.metadata.options.input_file_name, "w") as f:
            f.write(input_content)

        remote_files = None
        local_copy_list = None
        if isinstance(self.inputs.wf_folder, FolderData):
            local_copy_list = [
                (
                    self.inputs.wf_folder.uuid,
                    self.metadata.options.input_wf_name,
                    "fort.9",
                )
            ]
        elif isinstance(self.inputs.wf_folder, SinglefileData):
            local_copy_list = [
                (self.inputs.wf_folder.uuid, self.inputs.wf_folder.filename, "fort.9")
            ]
        else:
            remote_files = [
                (
                    self.inputs.wf_folder.computer.uuid,
                    os.path.join(
                        self.inputs.wf_folder.get_remote_path(),
                        self.metadata.options.input_wf_name,
                    ),
                    "fort.9",
                )
            ]

        return self.create_calc_info(
            tempfolder,
            local_copy_list=local_copy_list,
            remote_copy_list=remote_files,
            retrieve_list=self.get_retrieve_list(),
            retrieve_temporary_list=self.get_retrieve_temp_list(),
        )

    def create_calc_info(
        self,
        tempfolder,
        local_copy_list=None,
        remote_copy_list=None,
        remote_symlink_list=None,
        retrieve_list=None,
        retrieve_temporary_list=None,
    ):
        """Prepare CalcInfo object for aiida,
        to describe how the computation will be executed and recovered
        """
        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        if self.metadata.options.withmpi:
            # parallel versions of crystal (Pcrystal, Pproperties & MPPcrystal)
            # read data specifically from a file called INPUT
            if self.metadata.options.input_file_name != "INPUT":
                tempfolder.insert_path(
                    os.path.join(
                        tempfolder.abspath, self.metadata.options.input_file_name
                    ),
                    dest_name="INPUT",
                )
        else:
            codeinfo.stdin_name = self.metadata.options.input_file_name
        codeinfo.stdout_name = self.metadata.options.stdout_file_name
        # serial version output to stdout, but parallel version output to stderr!
        # so we join the files
        codeinfo.join_files = True
        codeinfo.cmdline_params = []
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list or []
        calcinfo.remote_copy_list = remote_copy_list or []
        calcinfo.remote_symlink_list = remote_symlink_list or []
        calcinfo.retrieve_list = retrieve_list or []
        calcinfo.retrieve_temporary_list = retrieve_temporary_list or []

        return calcinfo
