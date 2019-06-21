"""
Plugin to run GULP
"""
import os
import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.engine import CalcJob
from aiida.plugins import DataFactory


class GulpAbstractCalculation(CalcJob):
    """
    AiiDA calculation plugin to run the gulp executable,
    Subclasses must at least implement the
    ``get_input_creation_cls`` and ``get_retrieve_list`` methods,
    and specify a default ``metadata.options.parser_name`` in the spec
    """
    link_output_results = 'results'
    link_output_structure = 'structure'

    def get_input_creation(self):
        """ should return a class with a ``create_content`` method"""
        raise NotImplementedError

    def get_retrieve_list(self):
        """ should return the files to be retrieved """
        return [
            self.metadata.options.output_main_file_name
        ]

    @classmethod
    def define(cls, spec):

        super(GulpAbstractCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name',
                   valid_type=six.string_types, default='main.gin')
        spec.input('metadata.options.output_main_file_name',
                   valid_type=six.string_types, default='main.gout')

        spec.input(
            'structure', valid_type=DataFactory('structure'),
            required=True,
            help=('atomic structure used to create the '
                  'geometry section of .gin file content.'))
        spec.input(
            'potential', valid_type=DataFactory('gulp.potential'),
            required=True,
            help=('parameters to create the '
                  'potential section of the .gin file content.'))
        spec.input(
            'parameters', valid_type=DataFactory('dict'),
            required=False,
            help=('additional input parameters '
                  'to create the .gin file content.'))

        # TODO review aiidateam/aiida_core#2997, when closed, for exit code formalization

        # Unrecoverable errors: resources like the retrieved folder or its expected contents are missing
        spec.exit_code(
            200, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The retrieved folder data node could not be accessed.')
        spec.exit_code(
            210, 'ERROR_OUTPUT_FILE_MISSING',
            message='the main output file was not found')

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(
            300, 'ERROR_OUTPUT_PARSING',
            message=('An error was flagged trying to parse the '
                     'main gulp output file'))

        # Significant errors but calculation can be used to restart
        spec.exit_code(
            400, 'ERROR_GULP_RUN',
            message='The main gulp output file flagged an error')
        spec.exit_code(
            410, 'ERROR_NOT_OPTIMISED',
            message='The main gulp output file did not signal that an expected optimisation completed')

        spec.output(cls.link_output_results,
                    valid_type=DataFactory('dict'),
                    required=True,
                    help='the data extracted from the main output file')
        spec.default_output_node = cls.link_output_results

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """
        input_creation = self.get_input_creation()
        input_creation.create_content(
            self.inputs.structure,
            self.inputs.potential,
            self.inputs.get("parameters", None),
            self.inputs.get("symmetry", None)
        )
        content = input_creation.get_content()
        if not isinstance(content, six.text_type):
            content = six.u(content)
        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(content)

        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
        code = self.inputs.code
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.cmdline_params = [
            os.path.splitext(self.metadata.options.input_file_name)[0]
        ]
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = self.get_retrieve_list()
        calcinfo.retrieve_temporary_list = []

        return calcinfo
