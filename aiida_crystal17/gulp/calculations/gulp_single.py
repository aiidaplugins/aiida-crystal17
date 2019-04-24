import six
from aiida_crystal17.gulp.calculations.gulp_abstract import GulpAbstractCalculation
from aiida_crystal17.gulp.parsers.write_input import InputCreationSingle


class GulpSingleCalculation(GulpAbstractCalculation):
    """
    AiiDA calculation plugin to run the gulp executable,
    for single point energy calculations
    """

    def get_input_creation(self):
        return InputCreationSingle()

    @classmethod
    def define(cls, spec):

        super(GulpSingleCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='gulp.single')
