from aiida_crystal17.gulp.potentials.base import PotentialWriterAbstract
from aiida_crystal17.validation import load_schema
from aiida_crystal17.gulp.potentials.raw_reaxff import write_gulp_format


class PotentialWriterReaxff(PotentialWriterAbstract):
    """class for creating gulp reaxff type
    inter-atomic potential inputs
    """

    @classmethod
    def get_description(cls):
        return "ReaxFF potential"

    @classmethod
    def get_schema(cls):
        return load_schema("potential.reaxff.schema.json")

    @classmethod
    def _get_fitting_schema(cls):
        return load_schema("fitting.reaxff.schema.json")

    # pylint: disable=too-many-locals
    def _make_string(self, data, fitting_data=None):
        """write reaxff data in GULP input format

        :param data: dictionary of data
        :param species_filter: list of symbols to filter
        :rtype: str

        """
        return write_gulp_format(data, fitting_data=fitting_data)
