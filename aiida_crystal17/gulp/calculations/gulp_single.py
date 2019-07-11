import six
from aiida_crystal17.gulp.calculations.gulp_abstract import GulpAbstractCalculation
from aiida_crystal17.gulp.parsers.raw.write_input import InputCreationSingle


class GulpSingleCalculation(GulpAbstractCalculation):
    """
    AiiDA calculation plugin to run the gulp executable,
    for single point energy calculations
    """

    @classmethod
    def define(cls, spec):

        super(GulpSingleCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name',
                   valid_type=six.string_types, default='gulp.single')

    def create_input(self,
                     structure, potential,
                     parameters=None, symmetry=None):
        # TODO assert potential species contains at least one from structure
        input_creation = InputCreationSingle()
        input_creation.create_content(structure, potential.get_input_lines(), parameters, symmetry)
        return input_creation.get_content()
