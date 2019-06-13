"""
Plugin to create a CRYSTAL17 output file from a supplied input file.
"""
import six

from aiida.engine import CalcJob
from aiida.plugins import DataFactory


class CryAbstractCalculation(CalcJob):
    """
    AiiDA calculation plugin to run the runcry17 executable,
    Subclasses must at least specify input nodes,
    and implement a `prepare_for_submission` method
    """
    link_output_results = 'results'
    link_output_structure = 'structure'
    link_output_symmetry = 'symmetry'

    @classmethod
    def define(cls, spec):

        super(CryAbstractCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name',
                   valid_type=six.string_types, default='main.d12')
        spec.input('metadata.options.external_file_name',
                   valid_type=six.string_types, default='main.gui')
        spec.input('metadata.options.output_main_file_name',
                   valid_type=six.string_types, default='main.out')

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='crystal17.main')

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
                     'main crystal output file'))

        # Significant errors but calculation can be used to restart
        spec.exit_code(
            400, 'ERROR_CRYSTAL_RUN',
            message='The main crystal output file flagged an error')
        spec.exit_code(
            410, 'ERROR_SYMMETRY_INCONSISTENCY',
            message=('inconsistency in the input and output symmetry'))
        spec.exit_code(
            420, 'ERROR_SYMMETRY_NOT_FOUND',
            message=('primitive symmops were not found in the output file'))

        spec.output(cls.link_output_results,
                    valid_type=DataFactory('dict'),
                    required=True,
                    help='the data extracted from the main output file')
        spec.output(cls.link_output_structure,
                    valid_type=DataFactory('structure'),
                    required=False,
                    help='the structure output from the calculation')
        spec.output(cls.link_output_symmetry,
                    valid_type=DataFactory('crystal17.symmetry'),
                    required=False,
                    help='the symmetry data from the calculation')

        # TODO retrieve .f9 / .f98 from remote folder (for GUESSP or RESTART)
        # spec.input(
        #     'parent_folder', valid_type=RemoteData, required=False,
        #     help=('Use a remote folder as parent folder (for '
        #           'restarts and similar.'))
