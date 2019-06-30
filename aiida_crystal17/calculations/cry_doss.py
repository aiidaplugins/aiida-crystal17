import os
import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.engine import CalcJob
from aiida.plugins import DataFactory

from aiida_crystal17.parsers.raw.doss_input import create_doss_content
from aiida_crystal17.validation import validate_against_schema


def _validate_inputs(dict_data):
    validate_against_schema(dict_data.get_dict(), "doss_input.schema.json")


class CryDossCalculation(CalcJob):
    """
    AiiDA calculation plugin to run the runprop17 executable,
    for DOSS calculations.
    """
    @classmethod
    def define(cls, spec):
        super(CryDossCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name',
                   valid_type=six.string_types, default='main.doss.d3')
        spec.input('metadata.options.input_wf_name',
                   valid_type=six.string_types, default='main.f9')
        spec.input('metadata.options.symlink_wf',
                   valid_type=bool, default=True)
        spec.input('metadata.options.output_main_fname',
                   valid_type=six.string_types, default='main.doss.out')
        spec.input('metadata.options.output_f25_fname',
                   valid_type=six.string_types, default='main.doss.f25')

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='crystal17.doss')

        spec.input(
            'parameters', valid_type=DataFactory('dict'),
            required=True, validator=_validate_inputs,
            help='the input parameters to create the intput fort.d3 file.')
        spec.input(
            'wf_folder', valid_type=DataFactory('remote'),
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
            400, 'ERROR_DOSS_RUN',
            message='The DOSS crystal output file flagged an unhandled error')

        spec.output("results",
                    valid_type=DataFactory('dict'),
                    required=True,
                    help='summary of the parsed data')
        spec.default_output_node = "results"
        spec.output('arrays',
                    valid_type=DataFactory('array'),
                    required=False,
                    help='energies and DoS arrays')

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """

        input_lines = create_doss_content(self.inputs.parameters.get_dict())
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
            self.metadata.options.output_f25_fname
        ]
        calcinfo.retrieve_temporary_list = []

        return calcinfo
