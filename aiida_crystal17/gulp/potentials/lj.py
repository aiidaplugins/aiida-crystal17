import copy
from aiida_crystal17.gulp.potentials.base import PotentialWriterAbstract
from aiida_crystal17.gulp.potentials.common import filter_by_species
from aiida_crystal17.validation import load_schema


class PotentialWriterLJ(PotentialWriterAbstract):
    """class for creating gulp lennard-jones type
    inter-atomic potential inputs
    """
    _schema = None

    @classmethod
    def get_description(cls):
        return "Lennard-Jones potential"

    @classmethod
    def get_schema(cls):
        if cls._schema is None:
            cls._schema = load_schema("potential.lj.schema.json")
        return copy.deepcopy(cls._schema)

    def _make_string(self, data, species_filter=None):
        """write reaxff data in GULP input format

        :param data: dictionary of data
        :param species_filter: list of symbols to filter
        :rtype: str

        """
        if species_filter is not None:
            data = filter_by_species(data, species_filter)

        lines = []
        # TODO test that e.g. '1.2' and '2.1' aren't present, with different parameters

        for indices in sorted(data["2body"]):
            species = ["{:7s}".format(data["species"][int(i)]) for i in indices.split(".")]
            values = data["2body"][indices]
            lines.append("lennard {m} {n}".format(m=values.get("m", 12), n=values.get("n", 6)))
            if "rmin" in values:
                values_string = "{A} {B} {rmin} {rmax}".format(**values)
            else:
                values_string = "{A} {B} {rmax}".format(**values)

            lines.append(" ".join(species) + " " + values_string)

        return "\n".join(lines)
