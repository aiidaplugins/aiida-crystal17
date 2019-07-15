from collections import namedtuple
import copy
import re

from aiida_crystal17.validation import validate_against_schema
from aiida_crystal17.gulp.potentials.common import filter_by_species

PotentialContent = namedtuple('PotentialContent', ['content', 'number_of_flags', "number_flagged"])
"""used for returning the content creation for a potential

Parameters
----------
content: str
    the potential file content
number_of_flags: int
    number of potential flags for fitting
number_flagged: int
    number of variables flagged to fit

"""

RE_SYMBOL = "([A-Z][a-z]?)"
RE_SYMBOL_TYPE = "([A-Z][a-z]?)\\s+(\\bc\\b|\\bcore\\b|\\bs\\b|\\bshell\\b)"


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
        PotentialContent

        """
        raise NotImplementedError

    def create_content(self, data, species_filter=None, fitting_data=None):
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
        PotentialContent

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

    def read_exising(self, lines):
        """read an existing potential file

        Parameters
        ----------
        lines : list[str]

        Returns
        -------
        dict
            the potential data

        Raises
        ------
        IOError
            on parsing failure

        """
        raise NotImplementedError

    def _read_section(self, lines, lineno, breaking_terms, number_atoms, global_args=None):
        """read a section of a potential file, e.g.

        ::

            H core  He shell 1.00000000E+00 2.00000000E+00 12.00000 0 1
            H B 3.00000000E+00 4.00000000E+00 0.00 12.00000 1 0

        Parameters
        ----------
        lines : list[str]
            the lines in the file
        lineno : int
            the current line number, should be the line below the option line
        breaking_terms : list[str]
            stop reading lines, if a line starts with one of these terms
        number_atoms : the number of atoms expected
            [description]
        global_args : dict
            additional arguments to add to the result of each line

        Returns
        -------
        int: lineno
            the final line of the section
        set: species_set
            a set of species identified in the section
        dict: results
            {tuple[species]: {"values": str, "global": global_args}}

        Raises
        ------
        IOError
            If a parsing error occurs

        """
        results = {}
        symbol_set = set()

        while lineno < len(lines):
            line = lines[lineno]
            if any([line.strip().startswith(term) for term in breaking_terms]):
                break
            # TODO ignore comments at end of line
            match_sym_type = re.findall(
                "^{}\\s+(.+)\\s*$".format(
                    "\\s+".join([RE_SYMBOL_TYPE for _ in range(number_atoms)])),
                line.strip())
            match_sym = re.findall(
                "^{}\\s+(.+)\\s*$".format(
                    "\\s+".join([RE_SYMBOL for _ in range(number_atoms)])),
                line.strip())
            # TODO also match atomic numbers
            if match_sym_type:
                result = list(match_sym_type[0])
                index = []
                for _ in range(number_atoms):
                    symbol = result[0]
                    stype = {"c": "core", "s": "shell"}[result[1][0]]
                    index.append("{} {}".format(symbol, stype))
                    result = result[2:]
                results[tuple(index)] = {"values": result[0], "global": global_args}
            elif match_sym:
                result = list(match_sym[0])
                index = []
                for _ in range(number_atoms):
                    symbol = result[0]
                    index.append("{} {}".format(symbol, "core"))
                    result = result[1:]
                results[tuple(index)] = {"values": result[0], "global": global_args}
            else:
                raise IOError(
                    "expected line to be of form "
                    "'symbol1 <type> symbol2 <type> ... variables': {}".format(line))
            symbol_set.update(index)
            lineno += 1
        return lineno - 1, symbol_set, results
