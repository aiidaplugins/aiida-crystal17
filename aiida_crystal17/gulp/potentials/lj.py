from aiida_crystal17.gulp.potentials.base import PotentialWriterAbstract, PotentialContent
from aiida_crystal17.gulp.potentials.common import INDEX_SEP
from aiida_crystal17.validation import load_schema


class PotentialWriterLJ(PotentialWriterAbstract):
    """class for creating gulp lennard-jones type
    inter-atomic potential inputs
    """

    @classmethod
    def get_description(cls):
        return "Lennard-Jones potential, of the form; E = A/r**m - B/r**n"

    @classmethod
    def _get_schema(cls):
        return load_schema("potential.lj.schema.json")

    @classmethod
    def _get_fitting_schema(cls):
        return load_schema("fitting.lj.schema.json")

    def _make_string(self, data, fitting_data=None):
        """write reaxff data in GULP input format

        Parameters
        ----------
        data : dict
            dictionary of data
        species_filter : list[str] or None
            list of atomic symbols to filter by

        Returns
        -------
        str:
            the potential file content
        int:
            number of potential flags for fitting

        """
        lines = []
        total_flags = 0
        num_fit = 0

        for indices in sorted(data["2body"]):
            species = ["{:7s}".format(data["species"][int(i)]) for i in indices.split(INDEX_SEP)]
            values = data["2body"][indices]
            lines.append("lennard {lj_m} {lj_n}".format(lj_m=values.get("lj_m", 12), lj_n=values.get("lj_n", 6)))
            if "lj_rmin" in values:
                values_string = "{lj_A} {lj_B} {lj_rmin} {lj_rmax}".format(**values)
            else:
                values_string = "{lj_A} {lj_B} {lj_rmax}".format(**values)

            total_flags += 2

            if fitting_data is not None:
                flag_a = flag_b = 0
                if "lj_A" in fitting_data.get("2body", {}).get(indices, []):
                    flag_a = 1
                if "lj_B" in fitting_data.get("2body", {}).get(indices, []):
                    flag_b = 1
                num_fit += flag_a + flag_b
                values_string += " {} {}".format(flag_a, flag_b)

            lines.append(" ".join(species) + " " + values_string)

        return PotentialContent("\n".join(lines), total_flags, num_fit)
