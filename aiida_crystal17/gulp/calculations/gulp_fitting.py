""" a calculation plugin to perform fitting of potentials,
given a set of structures and observables
"""

import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import InputValidationError
from aiida.engine import CalcJob
from aiida.orm import Dict, StructureData
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.plugins import DataFactory

from aiida_crystal17.gulp.parsers.raw.write_input_fitting import create_input_lines


def potential_validator(potential):
    assert potential.has_fitting_flags, "fitting flags should be set for the potential"


class GulpFittingCalculation(CalcJob):
    """ a calculation plugin to perform fitting of potentials,
    given a set of structures and observables
    """
    @classmethod
    def define(cls, spec):
        """ define the process specification """
        super(GulpFittingCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name',
                   valid_type=six.string_types, default='main.gin')
        spec.input('metadata.options.output_main_file_name',
                   valid_type=six.string_types, default='main.gout')
        spec.input('metadata.options.output_stderr_file_name',
                   valid_type=six.string_types, default='main_stderr.txt')
        spec.input('metadata.options.output_dump_file_name',
                   valid_type=six.string_types, default='fitting.grs')
        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='gulp.fitting')

        spec.input(
            "potential", valid_type=DataFactory('gulp.potential'), required=True,
            serializer=to_aiida_type, validator=potential_validator,
            help=("a dictionary defining the potential. "
                  "Note this should have been created with fitting flags initialised")
        )

        spec.input_namespace(
            "structures", valid_type=StructureData, dynamic=True,
            help="a dict of structures to fit the potential to"
        )

        spec.input_namespace(
            "observables", valid_type=Dict, dynamic=True,
            help="a dictionary of observables for each structure"
        )

        # TODO review aiidateam/aiida_core#2997, when closed, for exit code formalization

        # Unrecoverable errors: resources like the retrieved folder or its expected contents are missing
        spec.exit_code(
            200, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The retrieved folder data node could not be accessed.')
        spec.exit_code(
            210, 'ERROR_OUTPUT_FILE_MISSING',
            message='the main (stdout) output file was not found')
        spec.exit_code(
            211, 'ERROR_TEMP_FOLDER_MISSING',
            message='the temporary retrieved folder was not found')

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(
            300, 'ERROR_PARSING_STDOUT',
            message=('An error was flagged trying to parse the '
                     'gulp exec stdout file'))
        spec.exit_code(
            301, 'ERROR_STDOUT_EMPTY',
            message=('The stdout file is empty'))
        spec.exit_code(
            310, 'ERROR_NOT_ENOUGH_OBSERVABLES',
            message=('The number of fitting variables exceeds the number of observables'))
        spec.exit_code(
            311, 'ERROR_FIT_UNSUCCESFUL',
            message=('The fit was not successful'))
        spec.exit_code(
            311, 'ERROR_GULP_UNKNOWN',
            message=('An error was flagged by GULP, which is not accounted for in another exit code'))

        # Significant errors but calculation can be used to restart

        spec.output(
            "results", valid_type=Dict, required=True,
            help="the data extracted from the main output file"
        )
        spec.default_output_node = "results"

        # TODO output a potential file (for input into GulpAbstractCalculation)

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """
        # validate that the structures and observables have the same keys
        struct_keys = set(self.inputs.structures.keys())
        observe_keys = set(self.inputs.observables.keys())
        if struct_keys != observe_keys:
            raise InputValidationError(
                "The structures and observables do not match: {} != {}".format(struct_keys, observe_keys))

        # TODO control observables

        # validate number of fitting variables vs number of observables
        if len(observe_keys) < self.inputs.potential.number_of_variables:
            raise InputValidationError(
                "The number of observables supplied ({}) "
                "is less than the number of variables required to be fit ({})".format(
                    len(observe_keys), self.inputs.potential.number_of_variables
                ))

        content = "\n".join(create_input_lines(
            self.inputs.potential,
            self.inputs.structures,
            self.inputs.observables,
            self.metadata.options.output_dump_file_name
        ))

        if not isinstance(content, six.text_type):
            content = six.u(content)
        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(content)

        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
        code = self.inputs.code
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.stdin_name = self.metadata.options.input_file_name
        codeinfo.stdout_name = self.metadata.options.output_main_file_name
        codeinfo.stderr_name = self.metadata.options.output_stderr_file_name
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [
            self.metadata.options.output_main_file_name,
            self.metadata.options.output_stderr_file_name,
            self.metadata.options.output_dump_file_name
        ]
        calcinfo.retrieve_temporary_list = []

        return calcinfo
