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
        return self._make_string(data, species_filter)
