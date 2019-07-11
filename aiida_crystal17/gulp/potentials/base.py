import copy

from aiida_crystal17.validation import validate_against_schema
from aiida_crystal17.gulp.potentials.common import filter_by_species


class PotentialWriterAbstract(object):
    """abstract class for creating gulp inter-atomic potential inputs,
    from a data dictionary.

    sub-classes should override the
    ``get_description``, ``get_schema`` and ``_make_string`` methods

    """
    _schema = None
    _fitting_schema = None

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
        # only load it once
        if cls._schema is None:
            cls._schema = cls._get_schema()
        return copy.deepcopy(cls._schema)

    @classmethod
    def _get_schema(cls):
        """return the schema to validate input data
        should be overridden by subclass

        Returns
        -------
        dict

        """
        raise NotImplementedError

    @classmethod
    def get_fitting_schema(cls):
        """return the schema to validate input data

        Returns
        -------
        dict

        """
        # only load it once
        if cls._fitting_schema is None:
            cls._fitting_schema = cls._get_fitting_schema()
        return copy.deepcopy(cls._fitting_schema)

    @classmethod
    def _get_fitting_schema(cls):
        """return the schema to validate input data
        should be overridden by subclass

        Returns
        -------
        dict

        """
        raise NotImplementedError

    def _make_string(self, data, fitting_data=None):
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

    def create_string(self, data, species_filter=None, fitting_data=None):
        """create string for inter-atomic potential section for main.gin file

        Parameters
        ----------
        data : dict
            dictionary of data required to create potential
        species_filter : list[str] or None
            list of atomic symbols to filter by
        fitting_data: dict or None
            a dictionary specifying which variables to flag for optimisation,
            of the form; {<type>: {<index>: [variable1, ...]}}
            if None, no flags will be added

        Returns
        -------
        str

        """
        # validate data
        schema = self.get_schema()
        validate_against_schema(data, schema)
        # test that e.g. '1-2' and '2-1' aren't present
        if "2body" in data:
            bonds = []
            for indices in data["2body"]:
                index_set = set(indices.split("-"))
                if index_set in bonds:
                    raise AssertionError(
                        "both {0}-{1} and {1}-{0} 2body keys exist in the data".format(*index_set))
                bonds.append(index_set)
        # test that e.g. '1-2-3' and '3-2-1' aren't present (2 is the pivot atom)
        if "3body" in data:
            angles = []
            for indices in data["3body"]:
                i1, i2, i3 = indices.split("-")
                if (i1, i2, i3) in angles:
                    raise AssertionError(
                        "both {0}-{1}-{2} and {2}-{1}-{0} 3body keys exist in the data".format(i1, i2, i3))
                angles.append((i1, i2, i3))
                angles.append((i3, i2, i1))

        if species_filter is not None:
            data = filter_by_species(data, species_filter)

        # validate fitting data
        if fitting_data is not None:
            fit_schema = self.get_fitting_schema()
            validate_against_schema(fitting_data, fit_schema)
            if species_filter is not None:
                fitting_data = filter_by_species(fitting_data, species_filter)
            if fitting_data["species"] != data["species"]:
                raise AssertionError("the fitting data species ({}) must be equal to the data species ({})".format(
                    fitting_data["species"], data["species"]
                ))
            # TODO same checks as main data and possibly switch 2body/3body indices to line up with those for main data

        return self._make_string(data, fitting_data=fitting_data)
