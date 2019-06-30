import os
import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import InputValidationError
from aiida.engine import CalcJob
from aiida.orm import RemoteData, Int, Float, Dict


def _validate_shrink(int_data):
    if not int_data.value > 0:
        raise InputValidationError("kpoint must be > 0")


class CryFermiCalculation(CalcJob):
    """
    AiiDA calculation plugin to run the runprop17 executable,
    for NEWK calculations (to return the fermi energy)
    """
    @classmethod
    def define(cls, spec):
        super(CryFermiCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name',
                   valid_type=six.string_types, default='main.fermi.d3')
        spec.input('metadata.options.input_wf_name',
                   valid_type=six.string_types, default='main.f9')
        spec.input('metadata.options.symlink_wf',
                   valid_type=bool, default=True)
        spec.input('metadata.options.output_main_fname',
                   valid_type=six.string_types, default='main.fermi.out')

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='crystal17.fermi')

        spec.input(
            'shrink_is', valid_type=Int,
            required=True, validator=_validate_shrink)
        spec.input(
            'shrink_isp', valid_type=Int,
            required=True, validator=_validate_shrink)
        spec.input(
            'wf_folder', valid_type=RemoteData,
            required=True,
            help='the folder containing the wavefunction fort.9 file')

        # TODO review aiidateam/aiida_core#2997, when closed, for exit code formalization

        # Unrecoverable errors: resources like the retrieved folder or its expected contents are missing
        spec.exit_code(
            200, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The retrieved folder data node could not be accessed.')
        spec.exit_code(
            210, 'ERROR_OUTPUT_FILE_MISSING',
            message='the DOSS output file was not found (fort.f25)')

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(
            300, 'ERROR_OUTPUT_PARSING',
            message=('An error was flagged trying to parse the '
                     'DOSS crystal output file (fort.f25)'))

        # Significant errors but calculation can be used to restart
        spec.exit_code(
            400, 'ERROR_NEWK_RUN',
            message='The NEWK crystal output file flagged an unhandled error')

        spec.output("fermi_energy",
                    valid_type=Float,
                    required=True,
                    help='The fermi energy (in eV)')
        spec.output("results",
                    valid_type=Dict,
                    required=True,
                    help='result from the parser')
        spec.default_output_node = "results"

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """

        input_lines = [
            "NEWK",
            "{} {}".format(self.inputs.shrink_is.value, self.inputs.shrink_isp.value),
            "1 0",
            "END"
        ]

        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(six.ensure_text("\n".join(input_lines)))

        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
        code = self.inputs.code
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.cmdline_params = [
            os.path.splitext(self.metadata.options.input_file_name)[0],
            os.path.splitext(self.metadata.options.input_wf_name)[0]
        ]
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []

        remote_files = [(
            self.inputs.wf_folder.computer.uuid,
            os.path.join(self.inputs.wf_folder.get_remote_path(),
                         self.metadata.options.input_wf_name),
            self.metadata.options.input_wf_name
        )]

        if self.metadata.options.symlink_wf:
            calcinfo.remote_symlink_list = remote_files
        else:
            calcinfo.remote_copy_list = remote_files

        calcinfo.retrieve_list = [
            self.metadata.options.output_main_fname,
            self.metadata.options.output_main_fname + "p"
        ]
        # note my local runprop copy outputs main.outp,
        # but on cx1 it outputs main.out
        calcinfo.retrieve_temporary_list = []

        return calcinfo
