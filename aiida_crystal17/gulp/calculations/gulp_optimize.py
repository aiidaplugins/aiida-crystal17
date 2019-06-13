import six
from aiida.plugins import DataFactory
from aiida_crystal17.gulp.calculations.gulp_abstract import GulpAbstractCalculation
from aiida_crystal17.gulp.parsers.write_input import InputCreationOpt


class GulpOptCalculation(GulpAbstractCalculation):
    """
    AiiDA calculation plugin to run the gulp executable,
    for single point energy calculations
    """
    def get_input_creation(self):
        return InputCreationOpt(
            outputs={"cif": self.metadata.options.out_cif_file_name}
        )

    def get_retrieve_list(self):
        """ should return the files to be retrieved """
        return [
            self.metadata.options.output_main_file_name,
            self.metadata.options.out_cif_file_name
        ]

    @classmethod
    def define(cls, spec):

        super(GulpOptCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='gulp.optimize')

        spec.input('metadata.options.out_cif_file_name',
                   valid_type=six.string_types, default='output.cif',
                   help="name of the cif file to output with final geometry")
        # spec.input('metadata.options.out_str_file_name',
        #            valid_type=six.string_types, default='output.str',
        #            help="name of the str file (i.e. a CRYSTAL98 .gui file)")

        spec.input(
            'symmetry', valid_type=DataFactory('dict'),
            required=False,
            help=('parameters to create the symmetry section of the '
                  '.gin file content (for constrained optimisation).'))

        spec.exit_code(
            150, 'ERROR_CIF_FILE_MISSING',
            message='the output cif file was not found')

        spec.output(cls.link_output_structure,
                    valid_type=DataFactory('structure'),
                    required=True,
                    help='the optimized structure output from the calculation')
