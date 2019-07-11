import copy

from aiida_crystal17.gulp.potentials.base import PotentialWriterAbstract
from aiida_crystal17.validation import load_schema
from aiida_crystal17.gulp.potentials.common import filter_by_species
from aiida_crystal17.gulp.potentials.raw_reaxff import write_gulp_format


class PotentialWriterReaxff(PotentialWriterAbstract):
    """class for creating gulp reaxff type
    inter-atomic potential inputs
    """
    _schema = None

    @classmethod
    def get_description(cls):
        return "ReaxFF potential"

    @classmethod
    def get_schema(cls):
        if cls._schema is None:
            cls._schema = load_schema("potential.reaxff.schema.json")
        return copy.deepcopy(cls._schema)

    # pylint: disable=too-many-locals
    def _make_string(self, data, species_filter=None):
        """write reaxff data in GULP input format

        :param data: dictionary of data
        :param species_filter: list of symbols to filter
        :rtype: str

        """
        if species_filter is not None:
            data = filter_by_species(data, species_filter)
        return write_gulp_format(data)
