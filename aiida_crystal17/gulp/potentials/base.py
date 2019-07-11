from aiida_crystal17.validation import validate_against_schema


class PotentialWriterAbstract(object):
    """abstract class for creating gulp inter-atomic potential inputs,
    from a data dictionary.

    sub-classes should override the
    ``get_description``, ``get_schema`` and ``_make_string`` methods

    """
    @classmethod
    def get_description(cls):
        """return description of the potential type"""
        return ""

    @classmethod
    def get_schema(cls):
        """return the schema to validate input data

        Returns
        -------
        dict

        """
        raise NotImplementedError

    def _make_string(self, data, species_filter=None):
        """create string for inter-atomic potential section for main.gin file

        Parameters
        ----------
        data : dict
            dictionary of data
        species_filter : list[str] or None
            list of atomic symbols to filter by

        Returns
        -------
        str

        """
        raise NotImplementedError

    def create_string(self, data, species_filter=None):
        """create string for inter-atomic potential section for main.gin file

        Parameters
        ----------
        data : dict
            dictionary of data
        species_filter : list[str] or None
            list of atomic symbols to filter by

        Returns
        -------
        str

        """
        schema = self.get_schema()
        validate_against_schema(data, schema)
        # test that e.g. '1-2' and '2-1' aren't present
        if "2body" in data:
            bonds = []
            for indices in data["2body"]:
                index_set = set(indices.split("-"))
                if index_set in bonds:
                    raise ValueError(
                        "both {0}-{1} and {1}-{0} 2body keys exist in the data".format(*index_set))
                bonds.append(index_set)
        # test that e.g. '1-2-3' and '3-2-1' aren't present (2 is the pivot atom)
        if "3body" in data:
            angles = []
            for indices in data["3body"]:
                i1, i2, i3 = indices.split("-")
                if (i1, i2, i3) in angles:
                    raise ValueError(
                        "both {0}-{1}-{2} and {2}-{1}-{0} 3body keys exist in the data".format(i1, i2, i3))
                angles.append((i1, i2, i3))
                angles.append((i3, i2, i1))
        return self._make_string(data, species_filter)
